import pystow
from bioregistry.analysis.bibliometrics import get_publications_df
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import pandas as pd
from sklearn.metrics import matthews_corrcoef, roc_auc_score
from sklearn.metrics import confusion_matrix

URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRPtP-tcXSx8zvhCuX6fqz_QvHowyAoDahnkixARk9rFTe0gfBN9GfdG6qTNQHHVL0i33XGSp_nV9XM/pub?gid=0&single=true&output=tsv"


def _map(s: str):
    if s in {"1", "1.0", 1, 1.0}:
        return True
    if s in {"0", "0.0", 0, 0.0}:
        return False
    raise ValueError(s)


def main():
    print("downloading curation")
    curation_df = pystow.ensure_csv("bioregistry", "analysis", url=URL, name="ben_curation.tsv")
    curation_df = curation_df[["pubmed", "title", "relevant"]]
    curation_df = curation_df[curation_df["relevant"].notna()]
    curation_df["label"] = curation_df["relevant"].map(_map)
    del curation_df["relevant"]

    print("loading bioregistry publications")
    publication_df = get_publications_df()
    publication_df = publication_df[publication_df.pubmed.notna()]
    publication_df = publication_df[["pubmed", "title"]]
    publication_df["label"] = True

    df = pd.concat([curation_df, publication_df])

    print("vectorizing")
    vectorizer = TfidfVectorizer()
    x = vectorizer.fit_transform(df.title)
    y = df.label

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


if __name__ == '__main__':
    main()
