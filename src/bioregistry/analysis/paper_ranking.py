"""Train a TF-IDF classifier and use it to score the relevance of new PubMed papers to the Bioregistry."""

from __future__ import annotations

import datetime
import json
from collections import defaultdict
from pathlib import Path

import click
import indra.literature.pubmed_client as pubmed_client
import numpy as np
import pandas as pd
from numpy.typing import NDArray
from sklearn.base import ClassifierMixin
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import matthews_corrcoef, roc_auc_score
from sklearn.model_selection import cross_val_predict, train_test_split
from sklearn.svm import SVC, LinearSVC
from sklearn.tree import DecisionTreeClassifier

from bioregistry.constants import BIOREGISTRY_PATH, CURATED_PAPERS_PATH

HERE = Path(__file__).parent.resolve()
ROOT = HERE.parent.parent.parent.resolve()

DIRECTORY = ROOT.joinpath("exports", "analyses", "paper_ranking")
DIRECTORY.mkdir(exist_ok=True, parents=True)

URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRPtP-tcXSx8zvhCuX6fqz_\
QvHowyAoDahnkixARk9rFTe0gfBN9GfdG6qTNQHHVL0i33XGSp_nV9XM/pub?output=csv"


def load_bioregistry_json(path: Path | None = None) -> pd.DataFrame:
    """Load bioregistry data from a JSON file, extracting publication details and fetching abstracts if missing.

    :param path: Path to the bioregistry JSON file.
    :return: DataFrame containing publication details.
    """
    if path is None:
        path = BIOREGISTRY_PATH
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        click.echo(f"JSONDecodeError: {e.msg}")
        click.echo(f"Error at line {e.lineno}, column {e.colno}")
        click.echo(f"Error at position {e.pos}")
        return pd.DataFrame()

    publications = []
    pmids_to_fetch = []
    for entry in data.values():
        if "publications" in entry:
            for pub in entry["publications"]:
                pmid = pub.get("pubmed")
                title = pub.get("title")
                if pmid:
                    pmids_to_fetch.append(pmid)
                publications.append({"pubmed": pmid, "title": title, "abstract": "", "label": 1})

    fetched_metadata = {}
    for chunk in [pmids_to_fetch[i : i + 200] for i in range(0, len(pmids_to_fetch), 200)]:
        fetched_metadata.update(pubmed_client.get_metadata_for_ids(chunk, get_abstracts=True))

    for pub in publications:
        if pub["pubmed"] in fetched_metadata:
            pub["abstract"] = fetched_metadata[pub["pubmed"]].get("abstract", "")

    click.echo(f"Got {len(publications):,} publications from the bioregistry")

    return pd.DataFrame(publications)


def load_curated_papers(file_path: Path = CURATED_PAPERS_PATH) -> pd.DataFrame:
    """Load curated papers data from TSV file, and fetch titles and abstracts for PMIDs.

    :param file_path: Path to the curated_papers.tsv file.
    :return: DataFrame containing curated publication details.
    """
    curated_df = pd.read_csv(file_path, sep="\t")
    curated_df = curated_df.rename(columns={"pmid": "pubmed", "relevant": "label"})
    curated_df["title"] = ""
    curated_df["abstract"] = ""

    pmids_to_fetch = curated_df["pubmed"].tolist()
    fetched_metadata = {}
    for chunk in [pmids_to_fetch[i : i + 200] for i in range(0, len(pmids_to_fetch), 200)]:
        fetched_metadata.update(pubmed_client.get_metadata_for_ids(chunk, get_abstracts=True))

    for index, row in curated_df.iterrows():
        if row["pubmed"] in fetched_metadata:
            curated_df.at[index, "title"] = fetched_metadata[row["pubmed"]].get("title", "")
            curated_df.at[index, "abstract"] = fetched_metadata[row["pubmed"]].get("abstract", "")

    click.echo(f"Got {len(curated_df)} curated publications from the curated_papers.tsv file")
    return curated_df


def fetch_pubmed_papers(curated_pmids: set[int]) -> pd.DataFrame:
    """Fetch PubMed papers from the last 30 days using specific search terms, excluding curated papers.

    :param curated_pmids: List containing already curated PMIDs
    :return: DataFrame containing PubMed paper details.
    """
    click.echo("Starting fetch_pubmed_papers")

    search_terms = ["database", "ontology", "resource", "vocabulary", "nomenclature"]
    paper_to_terms: defaultdict[str, list[str]] = defaultdict(list)

    for term in search_terms:
        pubmed_ids = pubmed_client.get_ids(term, use_text_word=True, reldate=30)
        for pubmed_id in pubmed_ids:
            if pubmed_id not in curated_pmids:
                paper_to_terms[pubmed_id].append(term)

    all_pmids = list(paper_to_terms.keys())
    click.echo(f"{len(all_pmids):,} articles found")
    if not all_pmids:
        click.echo(f"No articles found for the last 30 days with the search terms: {search_terms}")
        return pd.DataFrame()

    papers = {}
    for chunk in [all_pmids[i : i + 200] for i in range(0, len(all_pmids), 200)]:
        papers.update(pubmed_client.get_metadata_for_ids(chunk, get_abstracts=True))

    records = []
    for pubmed_id, paper in papers.items():
        title = paper.get("title")
        abstract = paper.get("abstract", "")

        if title and abstract:
            records.append(
                {
                    "pubmed": pubmed_id,
                    "title": title,
                    "abstract": abstract,
                    "year": paper.get("publication_date", {}).get("year"),
                    "search_terms": paper_to_terms.get(pubmed_id),
                }
            )

    click.echo(f"{len(records):,} records fetched from PubMed")
    return pd.DataFrame(records)


def load_curation_data() -> pd.DataFrame:
    """Download and load curation data from a Google Sheets URL.

    :return: DataFrame containing curated publication details.
    """
    click.echo("Downloading curation sheet")
    df = pd.read_csv(URL)
    df["label"] = df["relevant"].map(_map_labels)
    df = df[["pubmed", "title", "abstract", "label"]]

    pmids_to_fetch = df[df["abstract"] == ""].pubmed.tolist()
    fetched_metadata = {}
    for chunk in [pmids_to_fetch[i : i + 200] for i in range(0, len(pmids_to_fetch), 200)]:
        fetched_metadata.update(pubmed_client.get_metadata_for_ids(chunk, get_abstracts=True))

    for index, row in df.iterrows():
        if row["pubmed"] in fetched_metadata:
            df.at[index, "abstract"] = fetched_metadata[row["pubmed"]].get("abstract", "")

    click.echo(f"Got {df.label.notna().sum()} curated publications from Google Sheets")
    return df


def _map_labels(s: str) -> int | None:
    """Map labels to binary values.

    :param s: Label value.
    :return: Mapped binary label value.
    """
    if s in {"1", "1.0", 1}:
        return 1
    if s in {"0", "0.0", 0}:
        return 0
    return None


Classifiers = list[tuple[str, ClassifierMixin]]


def train_classifiers(x_train: NDArray[np.float64], y_train: NDArray[np.str_]) -> Classifiers:
    """Train multiple classifiers on the training data.

    :param x_train: Training features.
    :param y_train: Training labels.
    :return: List of trained classifiers.
    """
    classifiers = [
        ("rf", RandomForestClassifier()),
        ("lr", LogisticRegression()),
        ("dt", DecisionTreeClassifier()),
        ("svc", LinearSVC()),
        ("svm", SVC(kernel="rbf", probability=True)),
    ]
    for _, clf in classifiers:
        clf.fit(x_train, y_train)
    return classifiers


def generate_meta_features(
    classifiers: Classifiers, x_train: NDArray[np.float64], y_train: NDArray[np.str_]
) -> pd.DataFrame:
    """Generate meta-features for training a meta-classifier using cross-validation predictions.

    :param classifiers: List of trained classifiers.
    :param x_train: Training features.
    :param y_train: Training labels.
    :return: DataFrame containing meta-features.
    """
    meta_features = pd.DataFrame()
    for name, clf in classifiers:
        if hasattr(clf, "predict_proba"):
            predictions = cross_val_predict(clf, x_train, y_train, cv=5, method="predict_proba")[
                :, 1
            ]
        else:
            predictions = cross_val_predict(clf, x_train, y_train, cv=5, method="decision_function")
        meta_features[name] = predictions
    return meta_features


def evaluate_meta_classifier(
    meta_clf: ClassifierMixin, x_test_meta: NDArray[np.float64], y_test: NDArray[np.str_]
) -> tuple[float, float]:
    """Evaluate meta-classifier using MCC and AUC-ROC scores.

    :param meta_clf: Trained meta-classifier.
    :param x_test_meta: Test meta-features.
    :param y_test: Test labels.
    :return: MCC and AUC-ROC scores.
    """
    y_pred = meta_clf.predict(x_test_meta)
    mcc = matthews_corrcoef(y_test, y_pred)
    roc_auc = roc_auc_score(y_test, meta_clf.predict_proba(x_test_meta)[:, 1])
    return mcc, roc_auc


def truncate_text(text: str, max_length: int) -> str:
    """Truncate text to a specified maximum length."""
    # FIXME replace with builtin textwrap function
    return text if len(text) <= max_length else text[:max_length] + "..."


def predict_and_save(
    df: pd.DataFrame,
    vectorizer: TfidfVectorizer,
    classifiers: Classifiers,
    meta_clf: ClassifierMixin,
    filename: str | Path,
) -> None:
    """Predict and save scores for new data using trained classifiers and meta-classifier.

    :param df: DataFrame containing new data.
    :param vectorizer: Trained TF-IDF vectorizer.
    :param classifiers: List of trained classifiers.
    :param meta_clf: Trained meta-classifier.
    :param filename: Filename to save the predictions.
    """
    x_meta = pd.DataFrame()
    x_transformed = vectorizer.transform(df.title + " " + df.abstract)
    for name, clf in classifiers:
        if hasattr(clf, "predict_proba"):
            x_meta[name] = clf.predict_proba(x_transformed)[:, 1]
        else:
            x_meta[name] = clf.decision_function(x_transformed)

    df["meta_score"] = meta_clf.predict_proba(x_meta)[:, 1]
    df = df.sort_values(by="meta_score", ascending=False)
    df["abstract"] = df["abstract"].apply(lambda x: truncate_text(x, 25))
    df.to_csv(DIRECTORY.joinpath(filename), sep="\t", index=False)
    click.echo(f"Wrote predicted scores to {DIRECTORY.joinpath(filename)}")


def _first_of_month() -> str:
    today = datetime.date.today()
    return datetime.date(today.year, today.month, 1).isoformat()


@click.command()
@click.option(
    "--bioregistry-file",
    type=Path,
    help="Path to the bioregistry.json file",
)
@click.option(
    "--start-date",
    required=True,
    help="Start date of the period",
    default=_first_of_month,
)
@click.option(
    "--end-date",
    required=True,
    help="End date of the period",
    default=datetime.date.today().isoformat(),
)
def main(bioregistry_file: Path, start_date: str, end_date: str) -> None:
    """Load data, train classifiers, evaluate models, and predict new data.

    :param bioregistry_file: Path to the bioregistry JSON file.
    :param start_date: The start date of the period for which papers are being ranked.
    :param end_date: The end date of the period for which papers are being ranked.
    """
    publication_df = load_bioregistry_json(bioregistry_file)
    curation_df = load_curation_data()
    curated_papers_df = load_curated_papers(CURATED_PAPERS_PATH)

    # Combine all data sources
    df = pd.concat([curation_df, publication_df, curated_papers_df])
    df["abstract"] = df["abstract"].fillna("")
    df["title_abstract"] = df["title"] + " " + df["abstract"]

    vectorizer = TfidfVectorizer(stop_words="english")
    vectorizer.fit(df.title_abstract)

    annotated_df = df[df.label.notna()]
    x = vectorizer.transform(annotated_df.title_abstract)
    y = annotated_df.label

    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.33, random_state=42, shuffle=True
    )

    classifiers = train_classifiers(x_train, y_train)

    click.echo("Scoring individual classifiers")
    scores = []
    for name, clf in classifiers:
        y_pred = clf.predict(x_test)
        try:
            mcc = matthews_corrcoef(y_test, y_pred)
        except ValueError as e:
            click.secho(f"{clf} failed to calculate MCC: {e:.2f}", fg="yellow")
            mcc = None
        try:
            if hasattr(clf, "predict_proba"):
                roc_auc = roc_auc_score(y_test, clf.predict_proba(x_test)[:, 1])
            else:
                roc_auc = roc_auc_score(y_test, clf.decision_function(x_test))
        except AttributeError as e:
            click.secho(f"{clf} failed to calculate AUC-ROC: {e}", fg="yellow")
            roc_auc = None
        if not mcc and not roc_auc:
            continue
        scores.append((name, mcc or float("nan"), roc_auc or float("nan")))

    evaluation_df = pd.DataFrame(scores, columns=["classifier", "mcc", "auc_roc"]).round(3)
    click.echo(evaluation_df.to_markdown(index=False))

    meta_features = generate_meta_features(classifiers, x_train, y_train)
    meta_clf = LogisticRegression()
    meta_clf.fit(meta_features, y_train)

    x_test_meta = pd.DataFrame()
    for name, clf in classifiers:
        if hasattr(clf, "predict_proba"):
            x_test_meta[name] = clf.predict_proba(x_test)[:, 1]
        else:
            x_test_meta[name] = clf.decision_function(x_test)

    mcc, roc_auc = evaluate_meta_classifier(meta_clf, x_test_meta.to_numpy(), y_test)
    click.echo(f"Meta-Classifier MCC: {mcc:.2f}, AUC-ROC: {roc_auc:.2f}")
    new_row = {"classifier": "meta_classifier", "mcc": mcc, "auc_roc": roc_auc}
    evaluation_df = pd.concat([evaluation_df, pd.DataFrame([new_row])], ignore_index=True)

    evaluation_path = DIRECTORY.joinpath("evaluation.tsv")
    click.echo(f"Writing evaluation to {evaluation_path}")
    evaluation_df.to_csv(evaluation_path, sep="\t", index=False)

    random_forest_clf = classifiers[0][1]
    lr_clf = classifiers[1][1]
    importances_df = (
        pd.DataFrame(
            list(
                zip(
                    vectorizer.get_feature_names_out(),
                    vectorizer.idf_,
                    random_forest_clf.feature_importances_,
                    lr_clf.coef_[0],
                )
            ),
            columns=["word", "idf", "rf_importance", "lr_importance"],
        )
        .sort_values("rf_importance", ascending=False, key=abs)
        .round(4)
    )
    click.echo(importances_df.head(15).to_markdown(index=False))

    importance_path = DIRECTORY.joinpath("importances.tsv")
    click.echo(f"Writing feature (word) importances to {importance_path}")
    importances_df.to_csv(importance_path, sep="\t", index=False)

    # These have already been curated and will therefore be filtered out
    curated_pmids = set(curated_papers_df["pubmed"]).union(
        publication_df["pubmed"], curation_df["pubmed"]
    )

    new_pub_df = fetch_pubmed_papers(curated_pmids)
    if not new_pub_df.empty:
        filename = f"predictions_{start_date}_to_{end_date}.tsv"
        predict_and_save(new_pub_df, vectorizer, classifiers, meta_clf, filename)


if __name__ == "__main__":
    main()
