# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "bioregistry[paper-ranking]",
# ]
#
# [tool.uv.sources]
# bioregistry = { path = "../../../" }
# ///

"""Train a TF-IDF classifier and use it to score the relevance of new PubMed papers to the Bioregistry.

Run with:

1. ``python -m bioregistry.analysis.paper_ranking``
2. ``tox -e paper-ranking``
3. ``uv run --script paper_ranking.py``
"""

from __future__ import annotations

import datetime
import logging
import textwrap
from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple, TypeAlias, cast

import click
import numpy as np
import pandas as pd
from numpy.typing import NDArray
from sklearn.base import ClassifierMixin
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.linear_model._base import LinearClassifierMixin
from sklearn.metrics import matthews_corrcoef, roc_auc_score
from sklearn.model_selection import cross_val_predict, train_test_split
from sklearn.svm import SVC, LinearSVC
from sklearn.tree import DecisionTreeClassifier
from tqdm import tqdm

import bioregistry
from bioregistry import Manager
from bioregistry.constants import CURATED_PAPERS_PATH, EXPORT_DIRECTORY

if TYPE_CHECKING:
    import pubmed_downloader

logger = logging.getLogger(__name__)

DIRECTORY = EXPORT_DIRECTORY.joinpath("analyses", "paper_ranking")
DIRECTORY.mkdir(exist_ok=True, parents=True)

URL = (
    "https://docs.google.com/spreadsheets/d/e/2PACX-1vRPtP-tcXSx8zvhCuX6fqz_QvHowyAoDahnk"
    "ixARk9rFTe0gfBN9GfdG6qTNQHHVL0i33XGSp_nV9XM/pub?output=csv"
)

XTrain: TypeAlias = NDArray[np.float64]
YTrain: TypeAlias = NDArray[np.float64]
XTest: TypeAlias = NDArray[np.str_]
YTest: TypeAlias = NDArray[np.str_]

ClassifierHint: TypeAlias = ClassifierMixin | LinearClassifierMixin
Classifiers: TypeAlias = list[tuple[str, ClassifierHint]]

DEFAULT_SEARCH_TERMS: list[str] = [
    "database",
    "ontology",
    "resource",
    "vocabulary",
    "nomenclature",
]

#: A mapping from the NLM Catalog ID to the journal name for journals
#: that should be excluded
EXCLUDE_JOURNALS: dict[str, str] = {
    "101680187": "bioRxiv",
    "101767986": "medRxiv",
}


def get_publications_from_bioregistry(
    path: Path | None = None,
    *,
    loud: bool = True,
    strict: bool = False,
) -> pd.DataFrame:
    """Load bioregistry data from a JSON file, extracting publication details and fetching abstracts if missing.

    :param path: Path to the bioregistry JSON file.

    :returns: DataFrame containing publication details.
    """
    if path is not None:
        manager = Manager(registry=path)
    else:
        manager = bioregistry.manager

    publications = {}
    for resource in manager.registry.values():
        for publication in resource.get_publications():
            if not publication.pubmed:
                continue
            publications[publication.pubmed] = {
                "pubmed": str(publication.pubmed),
                "title": publication.title,
                "relevant": POSITIVE_VALUE,
            }

    df = pd.DataFrame.from_dict(publications, orient="index")
    _fill_abstracts(df, strict=strict)
    if loud:
        _echo_stats(df, "publications from the bioregistry")
    return df


def load_curated_papers(
    file_path: Path | None = None, *, loud: bool = True, strict: bool = False
) -> pd.DataFrame:
    """Load curated papers data from TSV file, and fetch titles and abstracts for PMIDs.

    :param file_path: Path to the curated_papers.tsv file.

    :returns: DataFrame containing curated publication details.
    """
    if file_path is None:
        file_path = CURATED_PAPERS_PATH

    df = pd.read_csv(file_path, sep="\t", dtype=str)
    df["relevant"] = df["relevant"].map(_map_labels)

    pubmed_to_article = _get_articles_dict(df)

    df["title"] = df["pubmed"].map(
        lambda pubmed: article.title if (article := pubmed_to_article.get(pubmed)) else None
    )
    _fill_abstracts(df, pubmed_to_article, strict=strict)
    if loud:
        _echo_stats(df, "curated publications from the curated_papers.tsv file")
    return df


def _echo_stats(df: pd.DataFrame, end: str) -> None:
    n_positive = (df["relevant"] == POSITIVE_VALUE).sum()
    n_negative = (df["relevant"] == NEGATIVE_VALUE).sum()
    n_uncurated = (~df["relevant"].isin({POSITIVE_VALUE, NEGATIVE_VALUE})).sum()
    n_total = len(df)
    click.echo(
        f"Got {n_total:,} (positive: {n_positive:,}, negative: {n_negative:,}, uncurated: {n_uncurated:,}) {end}"
    )


def _fill_abstracts(
    df: pd.DataFrame,
    pubmed_to_article: dict[str, pubmed_downloader.Article] | None = None,
    *,
    strict: bool = False,
) -> None:
    if pubmed_to_article is None:
        pubmed_to_article = _get_articles_dict(df)

    df["abstract"] = df["pubmed"].map(
        lambda pubmed: article.get_abstract()
        if (article := pubmed_to_article.get(pubmed))
        else None,
        na_action="ignore",
    )

    abstract_na_idx = df["abstract"].isna()
    if abstract_na_idx.all():
        raise ValueError(
            f"no abstracts were mapped properly.\n\n{df['pubmed'].nunique():,} PubMeds: {df['pubmed'].unique()}\n\nArticles: {pubmed_to_article}"
        )
    if strict and abstract_na_idx.any():
        raise ValueError(f"some abstracts weren't found\n\n{df[abstract_na_idx]}")


def _get_articles_dict(df: pd.DataFrame) -> dict[str, pubmed_downloader.Article]:
    import pubmed_downloader

    return pubmed_downloader.get_articles_dict(df["pubmed"], progress=True)


def _get_ids(
    term: str, *, use_text_word: bool, start_date: str, end_date: str | None = None
) -> list[str]:
    import pubmed_downloader

    if end_date is None:
        end_date = datetime.date.today().isoformat()

    return pubmed_downloader.search(
        term, use_text_word=use_text_word, mindate=start_date, maxdate=end_date
    )


def _search(
    terms: list[str],
    *,
    pubmed_ids_to_filter: set[str] | None = None,
    start_date: str,
    end_date: str | None = None,
) -> dict[str, list[str]]:
    if pubmed_ids_to_filter is None:
        pubmed_ids_to_filter = set()
    pubmed_to_terms: defaultdict[str, list[str]] = defaultdict(list)
    for term in tqdm(terms, desc="Searching PubMed", unit="search term", leave=False):
        for pubmed_id in _get_ids(
            term, use_text_word=True, start_date=start_date, end_date=end_date
        ):
            if pubmed_id not in pubmed_ids_to_filter:
                pubmed_to_terms[pubmed_id].append(term)
    return dict(pubmed_to_terms)


def fetch_pubmed_papers(
    *,
    pubmed_ids_to_filter: set[str] | None = None,
    start_date: str,
    end_date: str | None = None,
) -> pd.DataFrame:
    """Fetch PubMed papers from the last 30 days using specific search terms, excluding curated papers.

    :param pubmed_ids_to_filter: List containing already curated PMIDs.
    :param start_date: The start date of the period for which papers are being ranked.
    :param end_date: The end date of the period for which papers are being ranked.

    :returns: DataFrame containing PubMed paper details.
    """
    import pubmed_downloader

    pubmed_to_terms = _search(
        DEFAULT_SEARCH_TERMS,
        pubmed_ids_to_filter=pubmed_ids_to_filter,
        start_date=start_date,
        end_date=end_date,
    )
    click.echo(
        f"Search for {'/'.join(DEFAULT_SEARCH_TERMS)} return {len(pubmed_to_terms):,} articles"
    )

    articles = list(pubmed_downloader.get_articles(pubmed_to_terms, error_strategy="skip"))
    click.echo(f"Substantiated {len(articles):,} articles")

    records = []
    for article in articles:
        # Filter out papers that are from journals (typically
        # preprint servers that have PMIDs) to be excluded
        if article.journal.nlm_catalog_id in EXCLUDE_JOURNALS:
            continue
        title = article.title
        abstract = article.get_abstract()
        if title and abstract:
            records.append(
                {
                    "pubmed": str(article.pubmed),
                    "title": title,
                    "abstract": abstract,
                    "date": article.journal_issue.published
                    if article.journal_issue and article.journal_issue.published
                    else None,
                    "search_terms": pubmed_to_terms[str(article.pubmed)],
                }
            )

    click.echo(f"{len(records):,} records fetched from PubMed")
    return pd.DataFrame(records)


def load_google_curation_df(*, strict: bool = False, loud: bool = True) -> pd.DataFrame:
    """Download and load curation data from a Google Sheets URL.

    :returns: DataFrame containing curated publication details.
    """
    df = pd.read_csv(URL, dtype=str)
    df["relevant"] = df["relevant"].map(_map_labels)
    df = df[["pubmed", "title", "relevant"]]
    _fill_abstracts(df, strict=strict)
    if loud:
        _echo_stats(df, "curated publications from Google Sheets")
    return df


POSITIVE_VALUE = "yes"
NEGATIVE_VALUE = "no"


def _map_labels(s: str) -> str | None:
    """Standardize labels."""
    if pd.isna(s):
        return None
    if s in {"1", "1.0", 1, POSITIVE_VALUE}:
        return POSITIVE_VALUE
    if s in {"0", "0.0", 0, NEGATIVE_VALUE}:
        return NEGATIVE_VALUE
    return None


def train_classifiers(x_train: XTrain, y_train: YTrain) -> Classifiers:
    """Train multiple classifiers on the training data.

    :param x_train: Training features.
    :param y_train: Training labels.

    :returns: List of trained classifiers.
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
    classifiers: Classifiers, x_train: XTrain, y_train: YTrain, *, cv: int = 5
) -> pd.DataFrame:
    """Generate meta-features for training a meta-classifier using cross-validation predictions.

    .. todo:: explain what this approach is doing and why. What is a meta-feature?

    :param classifiers: List of trained classifiers.
    :param x_train: Training features.
    :param y_train: Training labels.
    :param cv: Number of folds for cross-validation

    :returns: DataFrame containing meta-features.
    """
    df = pd.DataFrame()
    for classifier_name, classifier in classifiers:
        df[classifier_name] = _cross_val_predict(classifier, x_train, y_train, cv=cv)
    return df


def _cross_val_predict(
    clf: ClassifierHint, x_train: XTrain, y_train: YTrain, cv: int
) -> NDArray[np.float64]:
    if not hasattr(clf, "predict_proba"):
        return cast(
            NDArray[np.float64],
            cross_val_predict(clf, x_train, y_train, cv=cv, method="decision_function"),
        )
    return cast(
        NDArray[np.float64],
        cross_val_predict(clf, x_train, y_train, cv=cv, method="predict_proba")[:, 1],
    )


def _predict(clf: ClassifierHint, x: NDArray[np.float64] | NDArray[np.str_]) -> NDArray[np.float64]:
    if hasattr(clf, "predict_proba"):
        return cast(NDArray[np.float64], clf.predict_proba(x)[:, 1])
    else:
        return cast(NDArray[np.float64], clf.decision_function(x))


class MetaClassifierEvaluationResults(NamedTuple):
    """A tuple for meta classifier results."""

    mcc: float
    roc_auc: float


def _evaluate_meta_classifier(
    meta_clf: ClassifierMixin, x_test_meta: XTest, y_test: YTest
) -> MetaClassifierEvaluationResults:
    """Evaluate meta-classifier using MCC and AUC-ROC scores.

    :param meta_clf: Trained meta-classifier.
    :param x_test_meta: Test meta-features.
    :param y_test: Test labels.

    :returns: MCC and AUC-ROC scores.
    """
    y_pred = meta_clf.predict(x_test_meta)
    mcc = matthews_corrcoef(y_test, y_pred)
    roc_auc = roc_auc_score(y_test, _predict(meta_clf, x_test_meta))
    return MetaClassifierEvaluationResults(mcc, roc_auc)


def predict_and_save(
    df: pd.DataFrame,
    vectorizer: TfidfVectorizer,
    classifiers: Classifiers,
    meta_clf: ClassifierMixin,
    path: str | Path,
) -> None:
    """Predict and save scores for new data using trained classifiers and meta-classifier.

    :param df: DataFrame containing new data.
    :param vectorizer: Trained TF-IDF vectorizer.
    :param classifiers: List of trained classifiers.
    :param meta_clf: Trained meta-classifier.
    :param path: Path to save the predictions.
    """
    x_meta = pd.DataFrame()
    x_transformed = vectorizer.transform(_concat(df))
    for name, clf in classifiers:
        x_meta[name] = _predict(clf, x_transformed)

    df["meta_score"] = _predict(meta_clf, x_meta.to_numpy())
    df = df.sort_values(by="meta_score", ascending=False)
    df["abstract"] = df["abstract"].apply(lambda x: textwrap.shorten(x, 50))
    path = Path(path).resolve()
    df.to_csv(path, sep="\t", index=False)
    click.echo(f"Wrote predicted scores to {path}")


def _first_of_month() -> str:
    today = datetime.date.today()
    return datetime.date(today.year, today.month, 1).isoformat()


def _get_meta_results(
    classifiers: Classifiers, x_train: XTrain, x_test: XTest, y_train: YTrain, y_test: YTest
) -> tuple[LogisticRegression, MetaClassifierEvaluationResults]:
    meta_features = generate_meta_features(classifiers, x_train, y_train)
    meta_clf = LogisticRegression()
    meta_clf.fit(meta_features, y_train)

    x_test_meta = pd.DataFrame()
    for name, clf in classifiers:
        x_test_meta[name] = _predict(clf, x_test)

    return meta_clf, _evaluate_meta_classifier(meta_clf, x_test_meta.to_numpy(), y_test)


def _get_evaluation_df(
    classifiers: Classifiers, x_train: XTrain, x_test: XTest, y_train: YTrain, y_test: YTest
) -> tuple[LogisticRegression, pd.DataFrame]:
    scores = []
    for name, clf in classifiers:
        y_pred = clf.predict(x_test)
        try:
            mcc = matthews_corrcoef(y_test, y_pred)
        except ValueError as e:
            tqdm.write(click.style(f"{clf} failed to calculate MCC: {e}", fg="yellow"))
            mcc = None
        roc_auc = roc_auc_score(y_test, _predict(clf, x_test))
        if not mcc and not roc_auc:
            continue
        scores.append((name, mcc or float("nan"), roc_auc or float("nan")))

    meta_clf, meta_clf_results = _get_meta_results(
        classifiers, x_train=x_train, y_train=y_train, x_test=x_test, y_test=y_test
    )
    scores.append(("meta_classifier", meta_clf_results.mcc, meta_clf_results.roc_auc))

    evaluation_df = pd.DataFrame(scores, columns=["classifier", "mcc", "auc_roc"]).round(3)
    return meta_clf, evaluation_df


@click.command()
@click.option(
    "--bioregistry-file",
    type=Path,
    help="Path to the bioregistry.json file. Defaults to internal",
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
@click.option("--directory", type=Path, default=DIRECTORY)
def main(bioregistry_file: Path | None, start_date: str, end_date: str, directory: Path) -> None:
    """Load data, train classifiers, evaluate models, and predict new data.

    :param bioregistry_file: Path to the bioregistry JSON file.
    :param start_date: The start date of the period for which papers are being ranked.
    :param end_date: The end date of the period for which papers are being ranked.
    """
    curated_pubmed_ids, vectorizer, classifiers, meta_clf = train(
        bioregistry_file=bioregistry_file,
        curated_papers_path=CURATED_PAPERS_PATH,
        output_path=directory,
    )
    predictions_df = fetch_pubmed_papers(
        pubmed_ids_to_filter=curated_pubmed_ids, start_date=start_date, end_date=end_date
    )
    if not predictions_df.empty:
        predictions_path = directory.joinpath("predictions.tsv")
        predict_and_save(predictions_df, vectorizer, classifiers, meta_clf, predictions_path)


class TrainingResult(NamedTuple):
    """The results from training."""

    curated_pubmed_ids: set[str]
    vectorizer: TfidfVectorizer
    classifiers: Classifiers
    meta_clf: LogisticRegression


def train(
    *,
    bioregistry_file: Path | None = None,
    curated_papers_path: Path | None = None,
    include_remote: bool = True,
    output_path: Path,
    loud: bool = True,
    strict: bool = False,
) -> TrainingResult:
    """Run training."""
    curated_dfs = [
        get_publications_from_bioregistry(bioregistry_file, loud=loud, strict=strict),
        load_curated_papers(curated_papers_path, loud=loud, strict=strict),
    ]
    if include_remote:
        curated_dfs.append(load_google_curation_df(strict=strict))

    df = pd.concat(curated_dfs)[["pubmed", "title", "abstract", "relevant"]]

    df["abstract"] = df["abstract"].fillna("")
    df["title_abstract"] = _concat(df)
    df = df[df.title_abstract.notna()]
    df = df.drop_duplicates()
    _echo_stats(df, "combine curated publications")

    if not (df["relevant"] == NEGATIVE_VALUE).sum():
        raise ValueError(f"no negative labels found. Values: {df['relevant'].unique()}")

    _echo_stats(df, "combine curated publications")

    vectorizer = TfidfVectorizer(stop_words="english")

    # do this after the vectorizer so we can still capture the text
    # from unannotated entries, e.g., from a Google Sheet
    annotated_df = df[df["relevant"].notna()]
    x = vectorizer.fit_transform(annotated_df.title_abstract)
    y = annotated_df["relevant"].map({POSITIVE_VALUE: True, NEGATIVE_VALUE: False}.__getitem__)

    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.33, random_state=42, shuffle=True
    )

    classifiers = train_classifiers(x_train, y_train)

    meta_clf, evaluation_df = _get_evaluation_df(
        classifiers, x_train=x_train, y_train=y_train, x_test=x_test, y_test=y_test
    )
    click.echo(evaluation_df.to_markdown(index=False))
    evaluation_path = output_path.joinpath("evaluation.tsv")
    click.echo(f"Writing evaluation to {evaluation_path}")
    evaluation_df.to_csv(evaluation_path, sep="\t", index=False)

    random_forest_clf = classifiers[0][1]
    lr_clf = classifiers[1][1]
    importances_df = (
        pd.DataFrame(
            zip(
                vectorizer.get_feature_names_out(),
                vectorizer.idf_,
                random_forest_clf.feature_importances_,
                lr_clf.coef_[0],
                strict=False,
            ),
            columns=["word", "idf", "rf_importance", "lr_importance"],
        )
        .sort_values("rf_importance", ascending=False, key=abs)
        .round(4)
    )
    click.echo(importances_df.head(15).to_markdown(index=False))
    importance_path = output_path.joinpath("importances.tsv")
    click.echo(f"Writing feature (word) importances to {importance_path}")
    importances_df.to_csv(importance_path, sep="\t", index=False)

    # These have already been curated and will therefore be filtered out
    curated_pubmed_ids: set[str] = {str(pubmed) for pubmed in df["pubmed"] if pd.notna(pubmed)}
    return TrainingResult(curated_pubmed_ids, vectorizer, classifiers, meta_clf)


def _concat(df: pd.DataFrame) -> pd.Series[str]:
    return cast("pd.Series[str]", df["title"]) + " " + cast("pd.Series[str]", df["abstract"])


if __name__ == "__main__":
    main()
