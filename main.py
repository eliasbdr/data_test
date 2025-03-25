import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import hashlib
from src import lecture, graphe,appliquer_operation


def main():
    st.title("Interactive Multi-File Analysis")
    st.subheader("Upload multiple files, configure data, and generate interactive plots")
    st.markdown("---")
    
    # Gestion des fichiers
    uploaded_files = st.file_uploader("Import Files", 
                                    type=['csv', 'txt', 'dat'],
                                    accept_multiple_files=True)
    
    if st.button("Reset All", type="secondary", use_container_width=True):
        # Supprimer toutes les clés de session
        keys_to_reset = ['file_configs', 'dataframes', 'colors', 'data_modified', 'file_configs_hash']
        for key in keys_to_reset:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()
    
    # Initialisation de la session
    if 'file_configs' not in st.session_state:
        st.session_state.file_configs = {}
    if 'dataframes' not in st.session_state:
        st.session_state.dataframes = []
    if 'colors' not in st.session_state:
        st.session_state.colors = []
    if 'data_modified' not in st.session_state:
        st.session_state.data_modified = False
    if 'file_configs_hash' not in st.session_state:
        st.session_state.file_configs_hash = None

    # Mise à jour des configurations
    if uploaded_files:
        current_files = set(st.session_state.file_configs.keys())
        new_files = {f.name for f in uploaded_files}
        
        # Supprimer les fichiers retirés
        for removed in current_files - new_files:
            del st.session_state.file_configs[removed]
        
        # Ajouter les nouveaux fichiers
        for f in uploaded_files:
            if f.name not in st.session_state.file_configs:
                st.session_state.file_configs[f.name] = {
                    'delimiter': ';',
                    'decimal': ',',
                    'color': "#%02x%02x%02x" % tuple(np.random.randint(0, 255, 3)),
                    'start_row': 0,
                    'header_row': 0,
                    'end_row': None
                }

    # Vérifier les changements de configuration
    if 'file_configs' in st.session_state:
        current_configs = st.session_state.file_configs
        current_hash = hashlib.md5(str(current_configs).encode()).hexdigest()
        
        if st.session_state.file_configs_hash != current_hash:
            st.session_state.data_modified = False
            st.session_state.file_configs_hash = current_hash

    # Chargement conditionnel des données
    if uploaded_files and not st.session_state.data_modified:
        dataframes = []
        colors = []
        
        for file_name, config in st.session_state.file_configs.items():
            file_obj = next(f for f in uploaded_files if f.name == file_name)
            df = lecture(file_obj, config['delimiter'], config['decimal'],
                        config['start_row'], config['end_row'], config['header_row'])
            if df is not None:
                dataframes.append(df)
                colors.append(config['color'])
        
        st.session_state.dataframes = dataframes
        st.session_state.colors = colors

    # Interface de configuration
    if uploaded_files:
        selected_file = st.selectbox("Selected File", 
                                   options=list(st.session_state.file_configs.keys()))
        
        with st.expander(f"Configuration: {selected_file}", expanded=True):
            config = st.session_state.file_configs[selected_file]
            
            col1, col2 = st.columns(2)
            with col1:
                config['delimiter'] = st.selectbox(
                    "Column Separator",
                    [',', ';', '\t', '|'],
                    key=f"del_{selected_file}",
                    index=1 if config['delimiter'] == ';' else 0
                )
                
                config['color'] = st.color_picker(
                    "Plot Color",
                    value=config['color'],
                    key=f"col_{selected_file}"
                )
            
            with col2:
                config['decimal'] = st.selectbox(
                    "Decimal Separator",
                    ['.', ','],
                    key=f"dec_{selected_file}",
                    index=1 if config['decimal'] == ',' else 0
                )
                
                config['header_row'] = st.number_input(
                    "Header Row",
                    min_value=0,
                    value=config['header_row'],
                    key=f"head_{selected_file}",
                    help="Row containing column titles"
                )
            
            st.markdown("**Row Selection**")
            col3, col4 = st.columns(2)
            with col3:
                config['start_row'] = st.number_input(
                    "First Data Row",
                    min_value=0,
                    value=config['start_row'],
                    key=f"start_{selected_file}",
                    help="First row of data to display"
                )
            
            with col4:
                config['end_row'] = st.number_input(
                    "Last Data Row",
                    min_value=config['start_row'],
                    value=config['end_row'] or config['start_row'] + 100,
                    key=f"end_{selected_file}"
                )
            
            # Prévisualisation des données
            file_obj = next(f for f in uploaded_files if f.name == selected_file)
            df = lecture(
                file_obj,
                config['delimiter'],
                config['decimal'],
                config['start_row'],
                config['end_row'],
                config['header_row']
            )
            
            if df is not None:
                st.markdown(f"**Data Preview ({df.shape[0]} rows, {df.shape[1]} columns)**")
                st.dataframe(df.head(3), use_container_width=True)

    # Section des opérations sur les colonnes
    if st.session_state.file_configs:
        st.markdown("---")
        st.subheader("Column Operations")
        
        separator = "||"
        all_columns = []
        all_column_options = []
        
        current_dataframes = st.session_state.dataframes
        
        for df in current_dataframes:
            file_name = df.attrs['file_name']
            for col in df.columns:
                col_id = f"{file_name}{separator}{col}"
                col_display = f"{file_name}: {col}"
                all_columns.append(col_id)
                all_column_options.append(col_display)
        
        options_map = dict(zip(all_column_options, all_columns))
        
        with st.container():
            col1, col2 = st.columns(2)
            
            with col1:
                col_display = st.multiselect(
                    "Select Columns to Process", 
                    all_column_options,
                    help="Select columns to apply the operation"
                )
                colonnes_selectionnees = [options_map[display] for display in col_display]
            
            with col2:
                operation = st.selectbox(
                    "Operation to Apply",
                    [
                        "addition", 
                        "multiplication", 
                        "division"
                    ],
                    help="Choose the operation to apply to selected columns"
                )
                
                param_label = {
                    "addition": "Value to Add",
                    "multiplication": "Multiplication Factor",
                    "division": "Divisor"
                }
                
                param = st.text_input(
                    param_label[operation],
                    "1"
                )
            


            if st.button("Apply Operation", type="secondary", key="apply_operation_btn",use_container_width=True):
                if not colonnes_selectionnees:
                    st.warning("Please select at least one column.")
                else:
                    try:
                        modified_dataframes = appliquer_operation(
                            current_dataframes, 
                            operation, 
                            colonnes_selectionnees, 
                            param
                        )
                        
                        # Vérifier que les modifications ont bien été appliquées
                        if len(modified_dataframes) == len(current_dataframes):
                            st.session_state.dataframes = modified_dataframes
                            st.session_state.data_modified = True
                            st.success(f"Operation '{operation}' applied successfully.")
                            st.rerun()
                        else:
                            st.error("Error: The number of dataframes changed unexpectedly.")
                            
                    except Exception as e:
                        st.error(f"Failed to apply operation: {str(e)}")
                        st.error("Please check that:")
                        st.error("- All selected columns contain numerical values")
                        st.error("- The parameter is a valid number")
                        st.error("- No division by zero is attempted")
            
            
            if st.button("Reset Calculations", 
            type="secondary", 
            help="Reset all column operations and restore original data",
            key="reset_calculations_btn", use_container_width=True):
                try:
                    if not uploaded_files:
                        st.warning("No files to reset!")
                    else:
                        # Réinitialiser les données
                        st.session_state.dataframes = []
                        for file_obj in uploaded_files:
                            config = st.session_state.file_configs[file_obj.name]
                            df = lecture(
                                file_obj,
                                config['delimiter'],
                                config['decimal'],
                                config['start_row'],
                                config['end_row'],
                                config['header_row']
                            )
                            if df is not None:
                                st.session_state.dataframes.append(df)
                        
                        st.session_state.data_modified = False
                        st.success("All calculations reset successfully!")
                        st.rerun()
                except Exception as e:
                    st.error(f"Reset failed: {str(e)}")

            # Espacement optionnel
            st.markdown("""<style>
            div[data-testid="stVerticalBlock"] > div:has(> div[data-testid="stVerticalBlock"] > div[data-testid="stButton"]) {
                gap: 0.5rem;
            }
</style>""", unsafe_allow_html=True)

    # Sélection des axes pour le graphique
    if st.session_state.dataframes:  # Modification clé : vérifier si des dataframes existent
        st.markdown("---")
        st.subheader("Axis Configuration")
        
        current_dataframes = st.session_state.dataframes
        
        separator = "||"
        all_columns = []
        all_column_options = []
        
        for df in current_dataframes:
            file_name = df.attrs['file_name']
            for col in df.columns:
                col_id = f"{file_name}{separator}{col}"
                col_display = f"{file_name}: {col}"
                all_columns.append(col_id)
                all_column_options.append(col_display)
        
        options_map = dict(zip(all_column_options, all_columns))
        
        col_x, col_y = st.columns(2)
        with col_x:
            x_display = st.multiselect("X Axis Selection", all_column_options, key="x_axis_select")
            x_axis = [options_map[display] for display in x_display] if x_display else []
        
        with col_y:
            y_display = st.multiselect("Y Axis Selection", all_column_options, key="y_axis_select")
            y_axis = [options_map[display] for display in y_display] if y_display else []
        
        col_x_label, col_y_label = st.columns(2)
        with col_x_label:
            x_label = st.text_input("Customize X Axis Label", "X Axis")
        
        with col_y_label:
            y_label = st.text_input("Customize Y Axis Label", "Y Axis")
        




        # Center the Generate Graph button
        if st.button("Generate Graph", type="secondary", key="generate_graph", use_container_width=True):
            if x_axis and y_axis:
                try:
                    fig = graphe(
                        current_dataframes, 
                        st.session_state.colors, 
                        x_axis, 
                        y_axis, 
                        x_label, 
                        y_label
                    )
                    
                    if fig is not None:
                        if fig is not None:
                            st.plotly_chart(
                                fig,
                                use_container_width=True,
                                config={'responsive': True},
                                height=700  # Hauteur initiale (sera écrasée par le CSS)
                            )
                    else:
                        st.warning("No valid graph could be generated. Check your axis selections.")
                except Exception as e:
                    st.error(f"Error generating graph: {str(e)}")
            else:
                st.warning("Please select X and Y axes before generating the graph")


if __name__ == "__main__":
    main()



