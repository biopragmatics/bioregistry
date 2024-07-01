"""Train a TF-IDF classifier and use it to score the relevance of new PubMed papers to the Bioregistry."""

import json
from pathlib import Path

import click
import indra.literature.pubmed_client as pubmed_client
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import matthews_corrcoef, roc_auc_score
from sklearn.model_selection import cross_val_predict, train_test_split
from sklearn.svm import SVC, LinearSVC
from sklearn.tree import DecisionTreeClassifier
from tabulate import tabulate

# Update the directory path to exports/analyses/auto_curation
BASE_DIRECTORY = Path("exports/analyses")
AUTO_CURATION_DIRECTORY = BASE_DIRECTORY.joinpath("auto_curation")
AUTO_CURATION_DIRECTORY.mkdir(exist_ok=True, parents=True)

URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRPtP-tcXSx8zvhCuX6fqz_\
       QvHowyAoDahnkixARk9rFTe0gfBN9GfdG6qTNQHHVL0i33XGSp_nV9XM/pub?output=csv"


def load_bioregistry_json(file_path):
    """Load bioregistry data from a JSON file, extracting publication details.

    :param file_path: Path to the bioregistry JSON file.
    :type file_path: str
    :return: DataFrame containing publication details.
    :rtype: pd.DataFrame
    """
    with open(file_path, "r") as f:
        data = json.load(f)
    publications = []
    for entry in data.values():
        if "publications" in entry:
            for pub in entry["publications"]:
                publications.append(
                    {"pubmed": pub.get("pubmed"), "title": pub.get("title"), "label": 1}
                )
    click.echo(f"Got {len(publications)} publications from the bioregistry")
    return pd.DataFrame(publications)


def fetch_pubmed_papers():
    """Fetch PubMed papers from the last 30 days using specific search terms.

    :return: DataFrame containing PubMed paper details.
    :rtype: pd.DataFrame
    """
    search_terms = ["database", "ontology", "resource", "vocabulary", "nomenclature"]
    paper_to_terms = {}

    for term in search_terms:
        pmids = pubmed_client.get_ids(term, use_text_word=True, reldate=30)
        for pmid in pmids:
            if pmid in paper_to_terms:
                paper_to_terms[pmid].append(term)
            else:
                paper_to_terms[pmid] = [term]

    all_pmids = list(paper_to_terms.keys())
    if not all_pmids:
        click.echo(f"No PMIDs found for the last 30 days with the search terms: {search_terms}")
        return pd.DataFrame()

    papers = {}
    for chunk in [all_pmids[i : i + 200] for i in range(0, len(all_pmids), 200)]:
        papers.update(pubmed_client.get_metadata_for_ids(chunk))

    records = [
        {
            "pubmed": paper.get("pmid"),
            "title": paper.get("title"),
            "year": paper.get("publication_date", {}).get("year"),
            "search_terms": paper_to_terms.get(paper.get("pmid")),
        }
        for paper in papers.values()
        if paper.get("title")
        and paper.get("pmid")
        and paper.get("publication_date", {}).get("year")
    ]
    return pd.DataFrame(records)


def load_curation_data():
    """Download and load curation data from a Google Sheets URL.

    :return: DataFrame containing curated publication details.
    :rtype: pd.DataFrame
    """
    click.echo("Downloading curation")
    df = pd.read_csv(URL)
    df["label"] = df["relevant"].map(_map_labels)
    df = df[["pubmed", "title", "label"]]
    click.echo(f"Got {df.label.notna().sum()} curated publications from Google Sheets")
    return df


def _map_labels(s: str):
    """Map labels to binary values.

    :param s: Label value.
    :type s: str
    :return: Mapped binary label value.
    :rtype: int
    """
    if s in {"1", "1.0", 1}:
        return 1
    if s in {"0", "0.0", 0}:
        return 0
    return None


def train_classifiers(x_train, y_train):
    """Train multiple classifiers on the training data.

    :param x_train: Training features.
    :type x_train: array-like
    :param y_train: Training labels.
    :type y_train: array-like
    :return: List of trained classifiers.
    :rtype: list
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


def generate_meta_features(classifiers, x_train, y_train):
    """Generate meta-features for training a meta-classifier using cross-validation predictions.

    :param classifiers: List of trained classifiers.
    :type classifiers: list
    :param x_train: Training features.
    :type x_train: array-like
    :param y_train: Training labels.
    :type y_train: array-like
    :return: DataFrame containing meta-features.
    :rtype: pd.DataFrame
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


def evaluate_meta_classifier(meta_clf, x_test_meta, y_test):
    """Evaluate the meta-classifier using MCC and AUC-ROC scores.

    :param meta_clf: Trained meta-classifier.
    :type meta_clf: classifier
    :param x_test_meta: Test meta-features.
    :type x_test_meta: array-like
    :param y_test: Test labels.
    :type y_test: array-like
    :return: MCC and AUC-ROC scores.
    :rtype: tuple
    """
    y_pred = meta_clf.predict(x_test_meta)
    mcc = matthews_corrcoef(y_test, y_pred)
    roc_auc = roc_auc_score(y_test, meta_clf.predict_proba(x_test_meta)[:, 1])
    return mcc, roc_auc


def predict_and_save(df, vectorizer, classifiers, meta_clf, filename):
    """Predict and save scores for new data using trained classifiers and meta-classifier.

    :param df: DataFrame containing new data.
    :type df: pd.DataFrame
    :param vectorizer: Trained TF-IDF vectorizer.
    :type vectorizer: TfidfVectorizer
    :param classifiers: List of trained classifiers.
    :type classifiers: list
    :param meta_clf: Trained meta-classifier.
    :type meta_clf: classifier
    :param filename: Filename to save the predictions.
    :type filename: str
    """
    x_meta = pd.DataFrame()
    x_transformed = vectorizer.transform(df.title)
    for name, clf in classifiers:
        if hasattr(clf, "predict_proba"):
            x_meta[name] = clf.predict_proba(x_transformed)[:, 1]
        else:
            x_meta[name] = clf.decision_function(x_transformed)

    df["meta_score"] = meta_clf.predict_proba(x_meta)[:, 1]
    df = df.sort_values(by="meta_score", ascending=False)
    df.to_csv(AUTO_CURATION_DIRECTORY.joinpath(filename), sep="\t", index=False)
    click.echo(f"Writing predicted scores to {AUTO_CURATION_DIRECTORY.joinpath(filename)}")


@click.command()
@click.option(
    "--bioregistry-file",
    default="src/bioregistry/data/bioregistry.json",
    help="Path to the bioregistry.json file",
)
def main(bioregistry_file):
    """Main function to load data, train classifiers, evaluate models, and predict new data.

    :param bioregistry_file: Path to the bioregistry JSON file.
    :type bioregistry_file: str
    """
    publication_df = load_bioregistry_json(bioregistry_file)
    curation_df = load_curation_data()

    # Combine both data sources
    df = pd.concat([curation_df, publication_df])
    df["title"] = df["title"].str.slice(0, 20)

    vectorizer = TfidfVectorizer(stop_words="english")
    vectorizer.fit(df.title)

    annotated_df = df[df.label.notna()]
    x = vectorizer.transform(annotated_df.title)
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
            click.secho(f"{clf} failed to calculate MCC: {e}", fg="yellow")
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
    evaluation_df.to_csv(AUTO_CURATION_DIRECTORY.joinpath("evaluation.tsv"), sep="\t", index=False)
    click.echo(tabulate(evaluation_df, showindex=False, headers=evaluation_df.columns))

    meta_features = generate_meta_features(classifiers, x_train, y_train)

    meta_clf = LogisticRegression()
    meta_clf.fit(meta_features, y_train)

    x_test_meta = pd.DataFrame()
    for name, clf in classifiers:
        if hasattr(clf, "predict_proba"):
            x_test_meta[name] = clf.predict_proba(x_test)[:, 1]
        else:
            x_test_meta[name] = clf.decision_function(x_test)

    mcc, roc_auc = evaluate_meta_classifier(meta_clf, x_test_meta, y_test)
    click.echo(f"Meta-Classifier MCC: {mcc}, AUC-ROC: {roc_auc}")

    random_forest_clf: RandomForestClassifier = classifiers[0][1]
    lr_clf: LogisticRegression = classifiers[1][1]
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
    click.echo(tabulate(importances_df.head(15), showindex=False, headers=importances_df.columns))

    importance_path = AUTO_CURATION_DIRECTORY.joinpath("importances.tsv")
    click.echo(f"Writing feature (word) importances to {importance_path}")
    importances_df.to_csv(importance_path, sep="\t", index=False)

    novel_df = df[~df.label.notna()][["pubmed", "title"]].copy()
    predict_and_save(novel_df, vectorizer, classifiers, meta_clf, "predictions_last_year.tsv")

    new_pub_df = fetch_pubmed_papers()
    if not new_pub_df.empty:
        predict_and_save(
            new_pub_df, vectorizer, classifiers, meta_clf, "predictions_last_month.tsv"
        )


if __name__ == "__main__":
    main()
