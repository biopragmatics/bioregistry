import pystow
from bioregistry.analysis.bibliometrics import get_publications_df
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import pandas as pd
from sklearn.metrics import matthews_corrcoef, roc_auc_score
from sklearn.metrics import confusion_matrix

URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRPtP-tcXSx8zvhCuX6fqz_QvHowyAoDahnkixARk9rFTe0gfBN9GfdG6qTNQHHVL0i33XGSp_nV9XM/pub?gid=0&single=true&output=tsv"
MODULE = pystow.module("bioregistry", "analysis")


def _map(s: str):
    if s in {"1", "1.0", 1, 1.0}:
        return 1
    if s in {"0", "0.0", 0, 0.0}:
        return 0
    return None


def main():
    print("loading bioregistry publications")
    publication_df = get_publications_df()
    publication_df = publication_df[publication_df.pubmed.notna()]
    publication_df = publication_df[["pubmed", "title"]]
    publication_df["label"] = True

    print("downloading curation")
    curation_df = MODULE.ensure_csv(url=URL, name="ben_curation.tsv")
    curation_df["label"] = curation_df["relevant"].map(_map)
    curation_df = curation_df[["pubmed", "title", "label"]]

    df = pd.concat([curation_df, publication_df])

    print("labels:", df.label.unique())

    print("training tf-idf")
    vectorizer = TfidfVectorizer()
    vectorizer.fit(df.title)

    print("applying tf-idf")
    annotation_idx = df.label.notna()
    annotated_df = df[annotation_idx]
    x = vectorizer.transform(annotated_df.title)
    y = annotated_df.label

    print("splitting")
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.33, random_state=42, shuffle=True
    )

    print("fitting")
    clf = RandomForestClassifier()
    clf.fit(x_train, y_train)

    print("scoring")
    y_pred = clf.predict(x_test)
    mcc = matthews_corrcoef(y_test, y_pred)
    roc_auc = roc_auc_score(y_test, clf.predict_log_proba(x_test)[:, 1])
    print(f"mcc: {mcc:.2f}, auc-roc: {roc_auc:.2f}")
    print(confusion_matrix(y_test, y_pred))

    print("predicting on unknowns")
    novel_df = df[~annotation_idx][["pubmed", "title"]].copy()
    novel_df["score"] = clf.predict_proba(vectorizer.transform(novel_df.title))[:, 1]
    novel_df = novel_df.sort_values("score", ascending=False)
    path = MODULE.join(name="results.tsv")
    print(f"writing to {path}")
    novel_df.to_csv(path, sep='\t', index=False)


if __name__ == '__main__':
    main()
