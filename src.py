import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import hashlib


def lecture(file, delimiter, decimal_separator, start_row, end_row=None, header_row=0):
    try:
        file.seek(0)
        header_df = pd.read_csv(file, delimiter=delimiter, decimal=decimal_separator,
                                skiprows=range(header_row), nrows=1, header=None, engine='python',
                                on_bad_lines='warn')
        
        column_names = header_df.iloc[0].tolist()
        
        seen = {}
        unique_column_names = []
        for i, col in enumerate(column_names):
            if col is None or pd.isna(col) or str(col).strip() == '':
                col = f"Colonne_{i+1}"
            if col in seen:
                seen[col] += 1
                unique_column_names.append(f"{col}_{seen[col]}")
            else:
                seen[col] = 0
                unique_column_names.append(col)
        
        file.seek(0)
        data_df = pd.read_csv(file, delimiter=delimiter, decimal=decimal_separator,
                               skiprows=range(start_row + header_row), nrows=end_row - start_row + 1 if end_row else None,
                               header=None, names=unique_column_names, engine='python', on_bad_lines='warn')
        
        data_df.attrs['file_name'] = file.name
        return data_df
    except Exception as e:
        st.error(f"Erreur de lecture du fichier {file.name}: {str(e)}")
        return None

def graphe(dataframes, colors, x_axis, y_axis, x_label=None, y_label=None):
    fig = go.Figure()
    separator = "||"
    for x_col in x_axis:
        for y_col in y_axis:
            try:
                x_file, x_col_name = x_col.split(separator, 1)
                y_file, y_col_name = y_col.split(separator, 1)
                x_df = next((df for df in dataframes if df.attrs['file_name'] == x_file), None)
                y_df = next((df for df in dataframes if df.attrs['file_name'] == y_file), None)
                color = next((color for df, color in zip(dataframes, colors) if df.attrs['file_name'] == x_file), '#000000')
                
                if x_df is not None and y_df is not None and x_col_name in x_df.columns and y_col_name in y_df.columns:
                    fig.add_trace(go.Scatter(
                        x=x_df[x_col_name],
                        y=y_df[y_col_name],
                        mode='lines+markers',
                        name=f"{x_file}: {x_col_name} vs {y_file}: {y_col_name}",
                        line=dict(color=color)
                    ))
            except (ValueError, KeyError) as e:
                st.warning(f"Erreur de combinaison {x_col}/{y_col}: {str(e)}")
    
    fig.update_layout(
        title="Visualisation Multi-Fichiers",
        xaxis_title=x_label or "Axe X",
        yaxis_title=y_label or "Axe Y",
        hovermode='x unified',autosize=True)
    
    return fig if fig.data else None

def appliquer_operation(dataframes, operation, colonnes_selectionnees, param=None):
    # Copier les dataframes pour ne pas modifier les originaux
    modified_dfs = []
    separator = "||"
    
    for df in dataframes:
        # Créer une copie du dataframe
        df_copy = df.copy()
        
        # Appliquer l'opération à chaque colonne sélectionnée
        for colonne in colonnes_selectionnees:
            file_name, col_name = colonne.split(separator, 1)
            
            # Vérifier si nous travaillons sur le bon dataframe
            if df_copy.attrs['file_name'] == file_name and col_name in df_copy.columns:
                try:
                    # Convertir la colonne en numérique si nécessaire
                    df_copy[col_name] = pd.to_numeric(df_copy[col_name], errors='coerce')
                    
                    if operation == 'addition':
                        value = float(param) if param else 0
                        new_col_name = f"{col_name}_plus{value}"
                        df_copy[new_col_name] = df_copy[col_name] + value
                        st.success(f"Addition de {value} appliquée sur {file_name}: {col_name}")
                    
                    elif operation == 'multiplication':
                        factor = float(param) if param else 1
                        new_col_name = f"{col_name}_x{factor}"
                        df_copy[new_col_name] = df_copy[col_name] * factor
                        st.success(f"Multiplication par {factor} appliquée sur {file_name}: {col_name}")
                        
                    elif operation == 'division':
                        divisor = float(param) if param else 1
                        if divisor == 0:
                            st.error(f"Impossible de diviser par zéro pour {file_name}: {col_name}")
                            continue
                        new_col_name = f"{col_name}_div{divisor}"
                        df_copy[new_col_name] = df_copy[col_name] / divisor
                        st.success(f"Division par {divisor} appliquée sur {file_name}: {col_name}")

                
                except Exception as e:
                    st.error(f"Erreur lors de l'application de l'opération '{operation}' sur {file_name}: {col_name}: {str(e)}")
        
        modified_dfs.append(df_copy)
    
    return modified_dfs