from __future__ import annotations

import pandas as pd
import streamlit as st

from app.services.csv_reader import (
    CSVReadError,
    dataframe_to_documents_auto,
    load_csv_dataframe,
)
from app.services.database import fetch_documents, save_documents
from app.services.document_loader import create_manual_document
from app.services.language_detector import language_label
from app.services.pdf_reader import PDFReadError, read_pdf
from app.services.text_cleaner import count_words


def _display_document_preview(documents: list) -> None:
    if not documents:
        return

    summary = pd.DataFrame(
        [
            {
                "ID": doc.document_id[:8],
                "Type": doc.input_type,
                "Titre": doc.title,
                "Langue": language_label(doc.language),
                "Source": doc.source,
                "Date": doc.publication_date,
                "Page": doc.page_number,
                "Mots": count_words(doc.text),
                "Caractères": len(doc.text),
            }
            for doc in documents
        ]
    )

    st.subheader("Aperçu des documents")
    st.dataframe(summary, width="stretch", hide_index=True)

    selected_index = st.selectbox(
        "Document à prévisualiser",
        options=list(range(len(documents))),
        format_func=lambda i: (
            f"{i + 1} — {documents[i].title or 'Sans titre'} "
            f"({language_label(documents[i].language)})"
        ),
    )

    doc = documents[selected_index]
    direction = "rtl" if doc.language == "ar" else "ltr"
    align = "right" if doc.language == "ar" else "left"

    st.markdown(
        f"""
        <div dir="{direction}" style="
            text-align:{align};
            background:white;
            border:1px solid #DDE3EA;
            border-radius:10px;
            padding:18px;
            max-height:420px;
            overflow-y:auto;
            line-height:1.8;
            white-space:pre-wrap;
        ">{doc.text[:15000]}</div>
        """,
        unsafe_allow_html=True,
    )

    if len(doc.text) > 15000:
        st.caption("L’aperçu est limité aux 15 000 premiers caractères.")

    if st.button(
        f"Enregistrer {len(documents)} document(s) dans la base",
        type="primary",
        width="stretch",
    ):
        inserted = save_documents(documents)
        st.success(f"{inserted} document(s) enregistré(s) avec succès.")


def render_ingestion_page() -> None:
    st.title("Import et préparation des articles")
    st.caption(
        "Importez un PDF, un CSV ou saisissez un article en français, arabe ou anglais."
    )

    if "prepared_documents" not in st.session_state:
        st.session_state.prepared_documents = []

    manual_tab, pdf_tab, csv_tab, database_tab = st.tabs(
        [
            "Saisie manuelle",
            "Import PDF",
            "Import CSV",
            "Documents enregistrés",
        ]
    )

    with manual_tab:
        col1, col2 = st.columns(2)
        with col1:
            title = st.text_input("Titre de l’article — facultatif")
            source = st.text_input("Source — facultative")
        with col2:
            publication_date = st.text_input(
                "Date de publication — facultative",
                placeholder="Détection automatique si elle apparaît dans le texte",
            )

        article_text = st.text_area(
            "Texte de l’article",
            height=300,
            placeholder=(
                "Collez ici un article économique en français, arabe ou anglais..."
            ),
        )

        if st.button("Préparer l’article", key="prepare_manual", type="primary"):
            try:
                document = create_manual_document(
                    text=article_text,
                    title=title,
                    source=source,
                    publication_date=publication_date,
                )
                st.session_state.prepared_documents = [document]
                st.success(
                    f"Article préparé — langue détectée : "
                    f"{language_label(document.language)}"
                )
            except ValueError as exc:
                st.error(str(exc))

    with pdf_tab:
        uploaded_pdf = st.file_uploader(
            "Choisir un fichier PDF",
            type=["pdf"],
            key="pdf_uploader",
        )

        col1, col2 = st.columns(2)
        with col1:
            pdf_source = st.text_input("Source du PDF — facultative", key="pdf_source")
        with col2:
            pdf_date = st.text_input(
                "Date de publication — facultative",
                key="pdf_date",
                placeholder="Détection automatique depuis le PDF",
            )

        narrative_only = st.checkbox(
            "Analyser uniquement le contenu narratif principal",
            value=True,
            help="Ignore la table des matières, les listes, les annexes et la bibliographie, puis conserve le PDF comme un document cohérent.",
        )

        if uploaded_pdf and st.button(
            "Extraire le texte du PDF",
            key="prepare_pdf",
            type="primary",
        ):
            try:
                documents = read_pdf(
                    uploaded_pdf,
                    source=pdf_source or None,
                    publication_date=pdf_date or None,
                    narrative_only=narrative_only,
                )
                st.session_state.prepared_documents = documents
                st.success(
                    f"{len(documents)} document cohérent préparé. Les annexes et éléments structurels ont été filtrés."
                )
            except PDFReadError as exc:
                st.error(str(exc))

    with csv_tab:
        uploaded_csv = st.file_uploader(
            "Choisir un fichier CSV",
            type=["csv"],
            key="csv_uploader",
        )

        if uploaded_csv:
            try:
                dataframe = load_csv_dataframe(uploaded_csv)
                st.success(
                    f"CSV lu correctement : {len(dataframe)} ligne(s), "
                    f"{len(dataframe.columns)} colonne(s)."
                )
                st.dataframe(dataframe.head(10), width="stretch")

                st.info(
                    "L’application détecte automatiquement les colonnes du texte, "
                    "du titre, de la source et de la date."
                )

                if st.button(
                    "Détecter et préparer automatiquement le CSV",
                    key="prepare_csv",
                    type="primary",
                ):
                    documents, schema = dataframe_to_documents_auto(
                        df=dataframe,
                        filename=uploaded_csv.name,
                    )

                    if not documents:
                        st.warning(
                            "Aucun article exploitable n’a été détecté."
                        )
                    else:
                        st.session_state.prepared_documents = documents
                        st.success(
                            f"{len(documents)} article(s) préparé(s). "
                            f"Colonne texte détectée : « {schema.text_column} »."
                        )

                        st.json(
                            {
                                "colonne_texte": schema.text_column,
                                "colonne_titre": schema.title_column,
                                "colonne_source": schema.source_column,
                                "colonne_date": schema.date_column,
                                "confiance_detection": schema.confidence,
                            }
                        )
            except CSVReadError as exc:
                st.error(str(exc))

    with database_tab:
        stored_documents = fetch_documents()

        if not stored_documents:
            st.info("Aucun document enregistré pour le moment.")
        else:
            stored_df = pd.DataFrame(stored_documents)
            stored_df["language"] = stored_df["language"].apply(language_label)
            stored_df = stored_df.rename(
                columns={
                    "document_id": "ID",
                    "input_type": "Type",
                    "title": "Titre",
                    "source": "Source",
                    "publication_date": "Date",
                    "language": "Langue",
                    "filename": "Fichier",
                    "page_number": "Page",
                    "created_at": "Importé le",
                    "text_length": "Caractères",
                }
            )
            st.dataframe(stored_df, width="stretch", hide_index=True)

    st.divider()

    _display_document_preview(st.session_state.prepared_documents)
