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




def graphe(dataframes, colors, x_axis, y_axis, x_label="X Axis", y_label="Y Axis"):
    fig = go.Figure()
    
    # 1. Configuration RESPONSIVE critique
    fig.update_layout(
        autosize=True,
        margin=dict(autoexpand=True, l=0, r=0, t=30, b=0),  # Marges minimales
    )
    
    # 2. Ajout des données (exemple adapté)
    for df, color in zip(dataframes, colors):
        file_name = df.attrs.get('file_name', 'unknown')
        for x_col, y_col in zip(x_axis, y_axis):
            if x_col.startswith(file_name + "||") and y_col.startswith(file_name + "||"):
                x_name = x_col.split("||")[1]
                y_name = y_col.split("||")[1]
                fig.add_trace(go.Scatter(
                    x=df[x_name],
                    y=df[y_name],
                    mode='lines',
                    line=dict(width=2, color=color),
                ))
    
    # 3. Optimisation finale
    fig.update_layout(
        xaxis_title=x_label,
        yaxis_title=y_label,
        hovermode='x unified'
    )
    
    return fig






def appliquer_operation(dataframes, operation, colonnes_selectionnees, param):
    separator = "||"
    modified_dfs = []
    
    for df in dataframes:
        # Faire une copie profonde du DataFrame
        df_copy = df.copy(deep=True)
        file_name = df_copy.attrs.get('file_name', 'unknown')
        
        for col_selection in colonnes_selectionnees:
            if col_selection.startswith(file_name + separator):
                col_name = col_selection.split(separator)[1]
                if col_name in df_copy.columns:
                    try:
                        # Convertir la colonne en numérique si possible
                        df_copy[col_name] = pd.to_numeric(df_copy[col_name], errors='coerce')
                        param_value = float(param)
                        
                        if operation == "addition":
                            df_copy[col_name] = df_copy[col_name].add(param_value)
                        elif operation == "multiplication":
                            df_copy[col_name] = df_copy[col_name].mul(param_value)
                        elif operation == "division":
                            if param_value != 0:
                                df_copy[col_name] = df_copy[col_name].div(param_value)
                            else:
                                raise ValueError("Division by zero")
                                
                        # Conserver les métadonnées
                        df_copy.attrs['file_name'] = file_name
                        
                    except ValueError as e:
                        raise ValueError(f"Invalid parameter or column values in column {col_name}: {str(e)}")
                    except Exception as e:
                        raise Exception(f"Error processing column {col_name}: {str(e)}")
        
        modified_dfs.append(df_copy)
    
    return modified_dfs
