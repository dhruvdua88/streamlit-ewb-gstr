import streamlit as st
import pandas as pd

def load_excel(file):
    """Load Excel file and return as DataFrame"""
    if file.name.endswith(".xls"):
        df = pd.read_excel(file, dtype=str, engine="xlrd", header=0)
    else:
        df = pd.read_excel(file, dtype=str, engine="openpyxl", header=0)
    
    # Remove unnamed columns
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
    
    # Trim spaces from column names
    df.columns = df.columns.str.strip()
    
    return df

# Streamlit UI
st.title("EWB vs GSTR-1 Comparison Tool")

# Upload Files
col1, col2 = st.columns(2)
with col1:
    ewb_file = st.file_uploader("Upload EWB File (Excel)", type=["xls", "xlsx"])
with col2:
    gstr_file = st.file_uploader("Upload GSTR-1 File (Excel)", type=["xls", "xlsx"])

if ewb_file and gstr_file:
    # Load files
    ewb_df = load_excel(ewb_file)
    gstr_df = load_excel(gstr_file)
    
    st.write("### Sample Data from EWB")
    st.dataframe(ewb_df.head())
    
    st.write("### Sample Data from GSTR-1")
    st.dataframe(gstr_df.head())
    
    st.write("### EWB File Columns")
    st.write(ewb_df.columns.tolist())
    
    st.write("### GSTR-1 File Columns")
    st.write(gstr_df.columns.tolist())
    
    # Select Invoice Number Columns
    st.write("### Select Invoice Number Column")
    ewb_invoice_col = st.selectbox("EWB Invoice Column", ewb_df.columns, key='ewb_inv')
    gstr_invoice_col = st.selectbox("GSTR-1 Invoice Column", gstr_df.columns, key='gstr_inv')
    
    # Group GSTR-1 Data by Invoice Number
    numeric_cols = st.multiselect("Select Numeric Columns to Sum (GSTR-1)", gstr_df.columns, default=[])
    gstr_grouped = gstr_df.groupby(gstr_invoice_col).agg({
        **{col: 'sum' for col in numeric_cols},
        **{col: 'first' for col in gstr_df.columns if col not in numeric_cols + [gstr_invoice_col]}
    }).reset_index()
    
    # Select columns to compare
    st.write("### Select 3 Pairs of Columns to Compare")
    ewb_col1 = st.selectbox("EWB Column 1", ewb_df.columns, key='ewb_col1')
    gstr_col1 = st.selectbox("GSTR-1 Column 1", gstr_grouped.columns, key='gstr_col1')
    
    ewb_col2 = st.selectbox("EWB Column 2", ewb_df.columns, key='ewb_col2')
    gstr_col2 = st.selectbox("GSTR-1 Column 2", gstr_grouped.columns, key='gstr_col2')
    
    ewb_col3 = st.selectbox("EWB Column 3", ewb_df.columns, key='ewb_col3')
    gstr_col3 = st.selectbox("GSTR-1 Column 3", gstr_grouped.columns, key='gstr_col3')
    
    if st.button("Compare"):
        # Merge Data
        if all(col in ewb_df.columns for col in [ewb_col1, ewb_col2, ewb_col3]) and \
           all(col in gstr_grouped.columns for col in [gstr_col1, gstr_col2, gstr_col3]):
            ewb_filtered = ewb_df.set_index(ewb_invoice_col)
            gstr_filtered = gstr_grouped.set_index(gstr_invoice_col)
            comparison_df = ewb_filtered[[ewb_col1, ewb_col2, ewb_col3]].merge(
                gstr_filtered[[gstr_col1, gstr_col2, gstr_col3]],
                left_index=True, right_index=True, suffixes=("_EWB", "_GSTR"))
            
            # Identify mismatches and highlight them
            for e_col, g_col in zip([ewb_col1, ewb_col2, ewb_col3], [gstr_col1, gstr_col2, gstr_col3]):
                comparison_df[f"Mismatch_{e_col}"] = comparison_df[f"{e_col}_EWB"] != comparison_df[f"{g_col}_GSTR"]
            
            # Show results
            st.write("### Differences Report")
            st.dataframe(comparison_df)
        else:
            st.error("Selected columns do not exist in the dataset. Please check column names.")
        
        # Missing Invoices Report
        missing_in_ewb = set(gstr_grouped[gstr_invoice_col]) - set(ewb_df[ewb_invoice_col])
        missing_in_gstr = set(ewb_df[ewb_invoice_col]) - set(gstr_grouped[gstr_invoice_col])
        
        st.write("### Missing Invoices")
        st.write(f"Invoices in GSTR-1 but missing in EWB: {missing_in_ewb}")
        st.write(f"Invoices in EWB but missing in GSTR-1: {missing_in_gstr}")
