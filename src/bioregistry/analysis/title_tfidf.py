# -*- coding: utf-8 -*-

"""Train, evaluate, and apply a TF-IDF classifier on resources that should be curated by publication title."""

import click
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import matthews_corrcoef, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC, LinearSVC
from sklearn.tree import DecisionTreeClassifier
from tabulate import tabulate

from bioregistry.bibliometrics import get_publications_df
from bioregistry.constants import EXPORT_ANALYSES

DIRECTORY = EXPORT_ANALYSES.joinpath("title_tfidf")
DIRECTORY.mkdir(exist_ok=True, parents=True)

URL = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vRPtP-tcXSx8zvhCuX6fqz_QvHowyAoDahnkixARk9rFTe0gfBN9GfdG6qTNQHHVL0i33XGSp_nV9XM/pub?output=tsv"
)


@click.command()
def main() -> None:
    """Train, evaluate, and apply a TF-IDF classifier on resources that should be curated by publication title."""
    click.echo("loading bioregistry publications")
    publication_df = get_publications_df()
    # TODO extend to documents with only a DOI
    publication_df = publication_df[publication_df.pubmed.notna() & publication_df.title.notna()]
    publication_df = publication_df[["pubmed", "title"]]
    publication_df["label"] = True
    click.echo(f"got {publication_df.shape[0]} publications from the bioregistry")

    click.echo("downloading curation")
    curation_df = pd.read_csv(URL, sep="\t")
    curation_df["label"] = curation_df["relevant"].map(_map_labels)
    curation_df = curation_df[["pubmed", "title", "label"]]
    click.echo(f"got {curation_df.label.notna().sum()} curated publications from google sheets")

    df = pd.concat([curation_df, publication_df])

    click.echo("training tf-idf")
    vectorizer = TfidfVectorizer(stop_words="english")
    vectorizer.fit(df.title)

    click.echo("applying tf-idf")
    annotation_idx = df.label.notna()
    annotated_df = df[annotation_idx]
    x = vectorizer.transform(annotated_df.title)
    y = annotated_df.label

    click.echo("splitting")
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.33, random_state=42, shuffle=True
    )

    click.echo("fitting")
    classifiers = [
        RandomForestClassifier(),
        LogisticRegression(),
        DecisionTreeClassifier(),
        LinearSVC(),
        SVC(kernel="rbf"),
    ]

    click.echo("scoring")
    scores = []
    for clf in classifiers:
        clf.fit(x_train, y_train)
        y_pred = clf.predict(x_test)
        try:
            mcc = matthews_corrcoef(y_test, y_pred)
        except ValueError as e:
            click.secho(f"{clf} failed to calculate MCC: {e}", fg="yellow")
            mcc = None
        try:
            roc_auc = roc_auc_score(y_test, clf.predict_proba(x_test)[:, 1])
        except AttributeError as e:
            click.secho(f"{clf} failed to calculate AUC-ROC: {e}", fg="yellow")
            roc_auc = None
        if not mcc and not roc_auc:
            continue
        scores.append((clf.__class__.__name__, mcc or float("nan"), roc_auc or float("nan")))

    evaluation_df = pd.DataFrame(scores, columns=["classifier", "mcc", "auc_roc"]).round(3)
    evaluation_df.to_csv(DIRECTORY.joinpath("evaluation.tsv"), sep="\t", index=False)
    click.echo(tabulate(evaluation_df, showindex=False, headers=evaluation_df.columns))

    random_forest_clf: RandomForestClassifier = classifiers[0]
    lr_clf: LogisticRegression = classifiers[1]
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

    importance_path = DIRECTORY.joinpath("importances.tsv")
    click.echo(f"writing feature (word) importances to {importance_path}")
    importances_df.to_csv(importance_path, sep="\t", index=False)

    click.echo("predicting on unknowns")
    novel_df = df[~annotation_idx][["pubmed", "title"]].copy()
    novel_df["score"] = random_forest_clf.predict_proba(vectorizer.transform(novel_df.title))[:, 1]
    novel_df = novel_df.sort_values("score", ascending=False)
    path = DIRECTORY.joinpath("predictions.tsv")
    click.echo(f"writing predicted scores to {path}")
    novel_df.to_csv(path, sep="\t", index=False)


def _map_labels(s: str):
    if s in {"1", "1.0", 1, 1.0}:
        return 1
    if s in {"0", "0.0", 0, 0.0}:
        return 0
    return None


if __name__ == "__main__":
    main()
