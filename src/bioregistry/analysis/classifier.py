import pystow
from bioregistry.analysis.bibliometrics import get_publications_df
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRPtP-tcXSx8zvhCuX6fqz_QvHowyAoDahnkixARk9rFTe0gfBN9GfdG6qTNQHHVL0i33XGSp_nV9XM/pub?gid=0&single=true&output=tsv"


def _map(s: str):
    if s == "1":
        return True
    if s == "0":
        return False
    raise ValueError


def main():
    curation_df = pystow.ensure_csv("bioregistry", "analysis", url=URL)
    curation_df = curation_df[["pubmed", "title", "relevant"]]
    curation_df = curation_df[curation_df["relevant"].notna()]
    curation_df["label"] = curation_df["relevant"].map(_map)
    del curation_df["relevant"]

    publication_df = get_publications_df()
    publication_df = publication_df[publication_df.pubmed.notna()]
    publication_df = publication_df[["pubmed", "title"]]
    publication_df["label"] = True

    df = pd.concat([curation_df, publication_df])

    print("vectorizing")
    vectorizer = TfidfVectorizer()
    x = vectorizer.fit_transform(df.title)
    y = df.label

    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.33, random_state=42, shuffle=True
    )

    clf = RandomForestClassifier()
    clf.fit(x_train, y_train)

    score = clf.score(x_test, y_test)
    print("score", score)
