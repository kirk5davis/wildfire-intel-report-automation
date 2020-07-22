# script name: wildfire_intel_automation.py
# purpose: automate the summarization of data pulled from EIRS (spatial view)
# created by kdav490
# created on 05/10/2020
# created for: Sarak Krock (wildfire intel analyst)

# import modules
from __future__ import print_function
import os
import sys
import time
import pandas as pd
import numpy as np
import traceback
from functools import wraps
import matplotlib.pyplot as plt
from jinja2 import Environment, FileSystemLoader
import pdfkit  #good luck with this Josh
# import arcpy
import sitecustomize


TIMESTAMP = time.strftime("%Y%m%d_%H%M%S")
REPORT_DATE = time.strftime("%m/%d/%Y @ %H00")
PDF_TIMESTAMP = time.strftime("%Y%m%d_%H00")
LOG_FILE = None  # placeholder
ROPA_EMER_INCIDENT_SV = r"C:\dnr\20200508_wildfire_intel_automation\data\sample_data_temp.gdb\ropa_emer_incident_sv"
ROPA_REGION_BOUNDARIES = r"C:\dnr\20200508_wildfire_intel_automation\data\sample_data.gdb\ropa_region_boundaries"
CURRRENT_YEAR = 2020
TEMPLATE_DIR = r'C:\dnr\20200508_wildfire_intel_automation\templates'

PDFKIT_OPTIONS = {
    'page-size': 'Letter',
    'margin-top': '0in',
    'margin-right': '0in',
    'margin-bottom': '0in',
    'margin-left': '0in',
    'encoding': "UTF-8",
    'no-outline': None,
    'viewport-size': '1024x768'
}

def clean_pandas_table_html(input_html_string):
    return input_html_string.replace('style="text-align: right;', "").replace('border="1"',"").replace("dataframe", "table table-bordered table-sm").replace("<tr>\n      <th></th>\n      <th></th>\n      <th></th>\n \
   </tr>\n", "").replace("   <tr>\n      <th></th>\n      <th></th>\n    </tr>\n  ","")

# generic log/file logging
def log_to_log_and_console(func):
    """Decorate that log function so that it logs to the console and to file"""
    @wraps(func)
    def my_func(*args):
        print("{} - {}".format(time.ctime(), args[0]))
        print("{} - {}".format(time.ctime(), args[0]), file=LOG_FILE)
        LOG_FILE.flush()
    return my_func


@log_to_log_and_console
def log(stuff):
    return stuff


if __name__ == '__main__':

    try:

        # make runtime dirs, and start time variables
        root = r"C:\dnr\20200508_wildfire_intel_automation\runs"
        run_dir = os.path.join(root, "{}_wildfire_intel_automation_josh_testing".format(TIMESTAMP))
        
        os.mkdir(run_dir)
        LOG_FILE = open(os.path.join(run_dir, "runtime_log.txt"), 'a')
        log("script starting - runtime dir & gdb creation")

        # Josh - I commented out anything referencing arcpy/ArcGIS stuff!

        # out_gdb = os.path.join(run_dir, "output.gdb")
        # arcpy.CreateFileGDB_management(run_dir, "output.gdb")
        # log(arcpy.GetMessages())

        # # step 1) export fire stats for the year
        # log("copying the fire statistics layer for fires to date")
        # intel_query = "START_DT >= date '{}-01-01 00:00:00'".format(CURRRENT_YEAR)
        # intel_fc = os.path.join(out_gdb, "fire_stats_eirs_{}".format(TIMESTAMP))
        # arcpy.FeatureClassToFeatureClass_conversion(ROPA_EMER_INCIDENT_SV, out_gdb, "fire_stats_eirs_{}".format(TIMESTAMP), where_clause=intel_query)
        # log(arcpy.GetMessages())

        # # step 2) intersect with regions
        # log("intersecting fire intel with regions")
        # intel_regions_fc = os.path.join(out_gdb, "fire_stats_eirs_regions_{}".format(TIMESTAMP))
        # arcpy.Intersect_analysis([intel_fc, ROPA_REGION_BOUNDARIES], intel_regions_fc, "ALL")
        # log(arcpy.GetMessages())

        # # step 3) add east/west category field
        # log("calc east & west side of state values")
        # arcpy.AddField_management(intel_regions_fc, "WA_STATE_SIDE", "TEXT", 4)
        # log(arcpy.GetMessages())
        # with arcpy.da.UpdateCursor(intel_regions_fc, ["JURISDICT_LABEL_NM", "WA_STATE_SIDE"]) as u_cur:
        #     for row in u_cur:
        #         if row[0] in ['Southeast', 'Northeast']:
        #             row[1] = "Eastside"
        #         else:
        #             row[1] = "Westside"
        #         u_cur.updateRow(row)
        # del u_cur, row

        # # step 3) grab certain columns, convert to list of tuples, read into Pandas
        # log("pulling out needed data")
        # cols_needed = ["INCIDENT_NO", "INCIDENT_ID", "INCIDENT_NM", "JURISDICT_LABEL_NM", "WA_STATE_SIDE",
        #                 "COUNTY_LABEL_NM", "FIREGCAUSE_LABEL_NM", "START_DT", 
        #                 "ACRES_BURNED", "FIREEVNT_CLASS_LABEL_NM", "PROTECTION_TYPE",
        #                 "RES_ORDER_NO", "NON_DNR_RES_ORDER_NO", "LAT_COORD", "LON_COORD"]
        
        # data = [i for i in arcpy.da.SearchCursor(intel_regions_fc, cols_needed)]
        # df = pd.DataFrame.from_records(data, columns=cols_needed)
        # # add column count field for pivot aggregation
        # df["RESPONSE_COUNT"] = 1

        log("read pickled dataframe for Josh to mess with...")
        df = pd.read_pickle(r"C:\dnr\20200508_wildfire_intel_automation\data\eirs_data_for_josh.zip")

        # step 4) do the pivots
        # response statistic totals
        tbl_response_stats = pd.pivot_table(df, values=["RESPONSE_COUNT", "ACRES_BURNED"], index=["WA_STATE_SIDE"],
                     aggfunc={"RESPONSE_COUNT":np.sum, "ACRES_BURNED":np.sum}, fill_value=0, margins=True, margins_name="Totals")
        tbl_response_stats = tbl_response_stats.reindex(columns=["RESPONSE_COUNT", "ACRES_BURNED"])
        tbl_response_stats.columns = ["DNR Responses", "Response Acres"]
        tbl_response_stats.index.name = ""

        # dnr statistic totals
        # tbl_dnr_stats = df[(df["FIREEVNT_CLASS_LABEL_NM"] == 'Classified') & (df["PROTECTION_TYPE"] != None) & (df["PROTECTION_TYPE"] != 'DNR Assist Other Agency')].pivot_table(values=["RESPONSE_COUNT", "ACRES_BURNED"], index=["WA_STATE_SIDE"],
        #         aggfunc={"RESPONSE_COUNT":np.sum, "ACRES_BURNED":np.sum}, fill_value=0, margins=True, margins_name="Totals")
        tbl_dnr_stats = df[(df["FIREEVNT_CLASS_LABEL_NM"] == 'Classified')].pivot_table(values=["RESPONSE_COUNT", "ACRES_BURNED"], index=["WA_STATE_SIDE"],
                aggfunc={"RESPONSE_COUNT":np.sum, "ACRES_BURNED":np.sum}, fill_value=0, margins=True, margins_name="Totals")
        tbl_dnr_stats = tbl_dnr_stats.reindex(columns=["RESPONSE_COUNT", "ACRES_BURNED"])
        tbl_dnr_stats.columns = ["DNR Fires", "DNR Acres"]
        tbl_dnr_stats.index.name = ""
        
        # statewide general causes
        # tbl_dnr_causes = df[(df["FIREEVNT_CLASS_LABEL_NM"] == 'Classified') & (df["PROTECTION_TYPE"] != None) & (df["PROTECTION_TYPE"] != 'DNR Assist Other Agency')].pivot_table(values=["RESPONSE_COUNT"], index=["FIREGCAUSE_LABEL_NM"],
        #         aggfunc={"RESPONSE_COUNT":np.sum}, fill_value=0, margins=True, margins_name="Totals")
        tbl_dnr_causes = df[(df["FIREEVNT_CLASS_LABEL_NM"] == 'Classified')].pivot_table(values=["RESPONSE_COUNT"], index=["FIREGCAUSE_LABEL_NM"],
                 aggfunc={"RESPONSE_COUNT":np.sum}, fill_value=0, margins=True, margins_name="Totals")
        tbl_dnr_causes.columns = ["Count"]
        tbl_dnr_causes.index.name = ""


        # step 5) insert variables into template using Jinja2 and export report with PDFKit
        env = Environment(loader=FileSystemLoader(r'C:\dnr\20200508_wildfire_intel_automation\templates'))
        template = env.get_template("eirs_intel_report.html")
        template_vars = {"title": "Fire Statistics",
                            "response_pivot_table": clean_pandas_table_html(tbl_response_stats.to_html()),
                            "dnr_pivot_table": clean_pandas_table_html(tbl_dnr_stats.to_html()),
                            "causes_pivot_table": clean_pandas_table_html(tbl_dnr_causes.to_html()),
                            "time_of_report": REPORT_DATE,
                            "footer_time_of_report": time.ctime()}
        
        html_out = template.render(template_vars)
        out_pdf = os.path.join(run_dir, "eirs_report_{}.pdf".format(PDF_TIMESTAMP))
        
        # Josh - if you can get PDFKit to work on your Mac - this will export the final report.
        pdfkit.from_string(html_out, out_pdf, options=PDFKIT_OPTIONS)

        log("script completed")

    except Exception as e:
        log("Exception hit!: {}".format(e))
        traceback.print_exc(file=LOG_FILE)
        traceback.print_exc()
    finally:
        LOG_FILE.flush()
        LOG_FILE.close()
        # arcpy.CheckInExtension("Spatial")
# end of script