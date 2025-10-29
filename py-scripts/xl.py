import pandas as pd
import importlib
import sys
import os
sys.path.append(os.path.join(os.path.abspath(__file__ + "../../../")))
lf_report = importlib.import_module("py-scripts.lf_report")
df = pd.read_excel("txpower.xlsx",header=None)
df.columns = df.iloc[1]
df = df.drop([0, 1]).reset_index(drop=True)
print(df.head())
report = lf_report.lf_report(_results_dir_name="tx_power", _output_html="tx_power.html", _output_pdf="tx_power.pdf", _path='')
report_path_date_time = report.get_path_date_time()
report.set_title("Tx Power")
report.build_banner()
report.set_table_title("Tx Power")
test_info = {
    "Test Name": "Tx Power",
    "Outfile": "test001",
    "AP": "HFCL",
    "CC": "US",
    "RD": "US",
    "Band": "5g",
    "Channel": "36",
    "NSS": "2",
    "Bandwidth": "80",
    "Tx Power": "20 22 24"
}
# pass_fail_col = [col for col in df.columns if "PASS" in col][0]
pass_fail_col = [col for col in df.columns if "PASS" in col.replace(" ", "").replace("\n","")][0]
pass_count = (df[pass_fail_col] == "PASS").sum()
test_info["Tests Passed"] = "{}/{}".format(pass_count,len(df))
report.set_table_title("Test Configuration")
report.build_table_title()
report.test_setup_table(value="Test Setup", test_setup_data=test_info)
cols_split = 12
for i in range(0, len(df.columns), cols_split):
    subset = df.iloc[:, i:i+cols_split]
    report.set_table_dataframe(subset)
    report.build_table()
report.build_footer()
html_file = report.write_html()
print("returned file {}".format(html_file))
print(html_file)
report.write_pdf(_page_size='A3', _orientation='Landscape')
df.to_csv("txpower.csv", index=False)
