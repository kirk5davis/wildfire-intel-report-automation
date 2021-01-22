# encoding: utf-8
# script name: wildfire_intel_automation.py
# purpose: automate the summarization of data pulled from EIRS (spatial view)
# notes: queries have been adjusted multiple, <> cannot be used in def queries 
#           where values count potentially be NULL or they get excluded
# created by kdav490
# created on 05/10/2020
# created for: Sarak Krock (wildfire intel analyst)

# import modules
from __future__ import print_function
import os
import sys
import time
import datetime
import pandas as pd
import numpy as np
import traceback
import shutil
from functools import wraps
import matplotlib.pyplot as plt
import matplotlib.style as style
import matplotlib.patheffects as PathEffects
from jinja2 import Environment, FileSystemLoader
# import pdfkit  ## no longer used
import arcpy
# import sitecustomize
from dnr_email import send_email
from chrome_pdf_export import ChromePDF


TIMESTAMP = time.strftime("%Y%m%d_%H%M%S")
REPORT_DATE = time.strftime("%m/%d/%Y")
REPORT_DATE_SHORT = time.strftime("%m/%d")
PDF_TIMESTAMP = time.strftime("%Y%m%d_%H00")
LOG_FILE = None  # placeholder
NO_DATA_PLACEHOLDER_PNG = r"K:\projects\wildfire_intel_report_automation\templates\static\no-data-graph_5x8_land.png"
ROPA_EMER_INCIDENT_SV = r"\\dnr\divisions\rp_gis\users\kdav490\software\connection_files\kdav490_ropa.sde\ROPA.EMER_INCIDENT_SV"
FIRE_POINTS_MXD_PATH = r"\\dnr\divisions\rp_gis\projects\wildfire_intel_report_automation\mxd\fire_points_map_v10_6.mxd"
CURRENT_YEAR = datetime.datetime.now().year
EARLIEST_STAT_YEAR = (CURRENT_YEAR - 10)
CHROME_INSTALL_DIR = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"


def clean_pandas_table_html(input_html_string):
    return input_html_string.replace('style="text-align: right;', "").replace('border="1"',"").replace("dataframe", "table table-bordered table-sm").replace("<tr>\n      <th></th>\n      <th></th>\n      <th></th>\n \
   </tr>\n", "").replace("   <tr>\n      <th></th>\n      <th></th>\n    </tr>\n  ","")


def add_value_labels(ax, decimal=False, spacing=5):
    """Add labels to the end of each bar in a bar chart.

    Arguments:
        ax (matplotlib.axes.Axes): The matplotlib object containing the axes
            of the plot to annotate.
        spacing (int): The distance between the labels and the bars.
    """

    # For each bar: Place a label
    for rect in ax.patches:
        # Get X and Y placement of label from rect.
        y_value = rect.get_height()
        x_value = rect.get_x() + rect.get_width() / 2

        # Number of points between bar and label. Change to your liking.
        space = spacing
        # Vertical alignment for positive values
        va = 'bottom'

        # If value of bar is negative: Place label below bar
        if y_value < 0:
            # Invert space to place label below
            space *= -1
            # Vertically align label at top
            va = 'top'

        # Use Y value as label and format number with one decimal place
        if decimal:
            if y_value > 1000:
                new_val = float(y_value)/float(1000)
                label = "{:.1f}k".format(new_val)
            else:
                label = "{:.1f}".format(y_value)
        else:
            label = "{:.0f}".format(y_value)

        # Create annotation
        ax.annotate(
            label,                      # Use `label` as label
            (x_value, y_value),         # Place label at end of the bar
            xytext=(0, space),          # Vertically shift label by `space`
            textcoords="offset points", # Interpret `xytext` as offset in points
            ha='center',                # Horizontally center label
            va=va,                      # Vertically align label differently for
            path_effects=[PathEffects.withStroke(linewidth=3, foreground='w')], # path effects for halo
            size=8,
            )                            # positive and negative values.


def set_last_report_date_query():
    '''Needs to return a specific string for the date definition query for recent fire symbology'''
    # if datetime.datetime.now().weekday() == 0:
    #     time_delta = datetime.timedelta(3)
    # else:
    #     time_delta = datetime.timedelta(1)
    # change to always look back 72hrs -
    time_delta = datetime.timedelta(3)
    now_delta = datetime.datetime.now() - time_delta
    return "START_DT >= timestamp '{}-{}-{} 00:00:00'".format(str(now_delta.year), str(now_delta.month).zfill(2), str(now_delta.day).zfill(2))

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
        root = r"\\dnr\divisions\rp_gis\projects\wildfire_intel_report_automation\runs"
        run_dir = os.path.join(root, "{}_wildfire_intel_automation".format(TIMESTAMP))
        out_dir = os.path.join(run_dir, "_outputs")
        
        os.mkdir(run_dir)
        os.mkdir(out_dir)
        LOG_FILE = open(os.path.join(run_dir, "runtime_log.txt"), 'a')
        log("script starting - runtime dir & gdb creation")

        out_gdb = os.path.join(out_dir, "data.gdb")
        arcpy.CreateFileGDB_management(out_dir, "data.gdb")
        log(arcpy.GetMessages())

        # step 1) export fire stats for the year
        log("copying the fire statistics layer for fires to date")
        intel_query = "START_DT >= timestamp '{}-01-01 00:00:00'".format(CURRENT_YEAR)
        intel_fc = os.path.join(out_gdb, "fire_stats_eirs_{}".format(TIMESTAMP))
        arcpy.FeatureClassToFeatureClass_conversion(ROPA_EMER_INCIDENT_SV, out_gdb, "fire_stats_eirs_{}".format(TIMESTAMP), where_clause=intel_query)
        log(arcpy.GetMessages())

        log("copying fire statistics layers for fires since 2010")
        historic_intel_fc = os.path.join(out_gdb, "historic_stats_eirs_{}".format(TIMESTAMP))
        historic_query = "START_DT >= timestamp '{}-01-01 00:00:00'".format(EARLIEST_STAT_YEAR)
        arcpy.FeatureClassToFeatureClass_conversion(ROPA_EMER_INCIDENT_SV, out_gdb, os.path.basename(historic_intel_fc), where_clause=historic_query)
        log(arcpy.GetMessages())

        # step 2) intersect with regions
        # log("intersecting fire intel with regions")
        # intel_regions_fc = os.path.join(out_gdb, "fire_stats_eirs_regions_{}".format(TIMESTAMP))
        # arcpy.Intersect_analysis([intel_fc, ROPA_REGION_BOUNDARIES], intel_regions_fc, "ALL")
        # log(arcpy.GetMessages())
        
        # quick fix for step 2 by-pass
        intel_regions_fc = intel_fc

        # step 3) add east/west category field
        log("calc east & west side of state values")
        arcpy.AddField_management(intel_regions_fc, "WA_STATE_SIDE", "TEXT", 4)
        log(arcpy.GetMessages())
        with arcpy.da.UpdateCursor(intel_regions_fc, ["REGION_NAME", "WA_STATE_SIDE"]) as u_cur:
            for row in u_cur:
                if row[0] in ['SOUTHEAST', 'NORTHEAST']:
                    row[1] = "Eastside"
                else:
                    row[1] = "Westside"
                u_cur.updateRow(row)
        del u_cur, row

        # step 3) grab certain columns, convert to list of tuples, read into Pandas
        log("pulling out needed data")
        cols_needed = ["INCIDENT_NO", "INCIDENT_ID", "INCIDENT_NM", "REGION_NAME", "WA_STATE_SIDE",
                        "COUNTY_LABEL_NM", "FIREGCAUSE_LABEL_NM", "START_DT", 
                        "ACRES_BURNED", "FIREEVNT_CLASS_LABEL_NM", "PROTECTION_TYPE",
                        "RES_ORDER_NO", "NON_DNR_RES_ORDER_NO", "LAT_COORD", "LON_COORD"]
        
        data = [i for i in arcpy.da.SearchCursor(intel_regions_fc, cols_needed)]
        df = pd.DataFrame.from_records(data, columns=cols_needed)
        # add column count field for pivot aggregation
        df["RESPONSE_COUNT"] = 1

        # step 4) do the pivots
        # response statistic totals
        log("building response statistics pivot table")
        tbl_response_stats = pd.pivot_table(df, values=["RESPONSE_COUNT", "ACRES_BURNED"], index=["WA_STATE_SIDE"],
                     aggfunc={"RESPONSE_COUNT":np.sum, "ACRES_BURNED":np.sum}, fill_value=0, margins=True, margins_name="Total")
        tbl_response_stats = tbl_response_stats.reindex(columns=["RESPONSE_COUNT", "ACRES_BURNED"])
        tbl_response_stats.columns = ["DNR Responses", "Response Acres"]
        tbl_response_stats.index.name = ""
        tbl_response_stats[["DNR Responses"]] = tbl_response_stats[["DNR Responses"]].applymap(np.int64)

        # dnr statistic totals
        log("building DNR statistics pivot table")
        tbl_dnr_stats = df[(df["FIREEVNT_CLASS_LABEL_NM"] == 'Classified') & (df["PROTECTION_TYPE"] != 'DNR Assist Other Agency')].pivot_table(values=["RESPONSE_COUNT", "ACRES_BURNED"], index=["WA_STATE_SIDE"],
                aggfunc={"RESPONSE_COUNT":np.sum, "ACRES_BURNED":np.sum}, fill_value=0, margins=True, margins_name="Totals")
        tbl_dnr_stats = tbl_dnr_stats.reindex(columns=["RESPONSE_COUNT", "ACRES_BURNED"])
        tbl_dnr_stats.columns = ["DNR Fires", "DNR Acres"]
        tbl_dnr_stats.index.name = ""
        # clean up the float inherent in pivot table calcs
        tbl_dnr_stats[["DNR Fires"]] = tbl_dnr_stats[["DNR Fires"]].applymap(np.int64)
        
        # statewide general causes
        log("building general causes dataframe")
        tbl_dnr_causes = df[(df["FIREEVNT_CLASS_LABEL_NM"] == 'Classified') & (df["PROTECTION_TYPE"] != 'DNR Assist Other Agency')].pivot_table(values=["RESPONSE_COUNT"], index=["FIREGCAUSE_LABEL_NM"],
                aggfunc=np.sum, fill_value=0, margins=True, margins_name="Totals")
        tbl_dnr_causes[["RESPONSE_COUNT"]] = tbl_dnr_causes[["RESPONSE_COUNT"]].applymap(np.int64)
        tbl_dnr_causes.columns = ["Count"]
        tbl_dnr_causes.index.name = ""
        tbl_dnr_causes[["Count"]] = tbl_dnr_causes[["Count"]].applymap(np.int64)
        df_causes = df[((df["FIREEVNT_CLASS_LABEL_NM"] == 'Classified') & (df["PROTECTION_TYPE"] != 'DNR Assist Other Agency'))].groupby(["FIREGCAUSE_LABEL_NM"])["RESPONSE_COUNT"].sum()   
        cause_list = sorted([(i, df_causes.to_dict()[i]) for i in df_causes.to_dict()])
        cause_labels = "-".join([str(i[0]) for i in cause_list])
        cause_vals = [i[1] for i in cause_list]

        # # generate bar chart of causes
        # # set plot styling
        log("build bar chart of DNR fire causes")
        out_causes_plot = os.path.join(out_dir, "causes_graphic_{}.png".format(PDF_TIMESTAMP))
        style.use("ggplot")
        df_plotting = df[((df["FIREEVNT_CLASS_LABEL_NM"] == 'Classified') & (df["PROTECTION_TYPE"] != 'DNR Assist Other Agency'))]
        df_causes = df_plotting.groupby(["FIREGCAUSE_LABEL_NM"])["RESPONSE_COUNT"].sum()
        ## test for no data in early season, throws type error if empty
        try:
            ax1 = df_causes.plot(kind='bar', figsize=(8,5), color='#c80b2e', fontsize=8, rot=45)
            ax1.set_alpha(0.8)
            ax1.set_ylabel("Number of Fires", fontsize=15)
            ax1.set_xlabel("General Cause Category", fontsize=15)
            add_value_labels(ax1)
            fig = plt.gcf()
            plt.tight_layout()
            plt.draw()
            fig.savefig(out_causes_plot, dpi=600)
        except TypeError:
            log("no data available for bar chart, setting placeholder 'no data' image")
            out_causes_plot = NO_DATA_PLACEHOLDER_PNG

        # step 5) gather all data for a certain years
        log("gathering data for the last 10 years")
        year_historic_to_date_fire_count = {i+EARLIEST_STAT_YEAR:0 for i in range(11)}
        year_historic_to_date_acres_burned = {i+EARLIEST_STAT_YEAR:0.0 for i in range(11)}
        # updated query to address dropped null values in the PROTECTION_TYPE category
        historic_dnr_fires_query = "(PROTECTION_TYPE <> 'DNR Assist Other Agency' OR PROTECTION_TYPE IS NULL) AND FIREEVNT_CLASS_LABEL_NM = 'Classified'"
        test_bad_vals = list()
        with arcpy.da.SearchCursor(historic_intel_fc, ["OBJECTID", "START_DT", "ACRES_BURNED"], historic_dnr_fires_query) as s_cur:
            today_dt = datetime.datetime.today()
            for row in s_cur:
                # updated logic 06/16/2020 - this was causing issues
                # same month logic
                # had to put pythonic hard filter on DNR - using <> in a query for a field that contains nulls resulted
                # in excluded values
                if row[1].month == today_dt.month and row[1].day <= today_dt.day:
                    year_historic_to_date_fire_count[row[1].year] += 1
                    year_historic_to_date_acres_burned[row[1].year] += row[2]
                # less than todays month logic
                if row[1].month < today_dt.month:
                    year_historic_to_date_fire_count[row[1].year] += 1
                    year_historic_to_date_acres_burned[row[1].year] += row[2]

        acres_burned_sort = sorted(year_historic_to_date_acres_burned.items())   
        fire_count_sort = sorted(year_historic_to_date_fire_count.items())
        x_acres_burned, y_acres_burned = zip(*acres_burned_sort)
        x_fire_count, y_fire_count = zip(*fire_count_sort)

        log("building bar charts for last 10 year graphics")
        log("---fire counts chart")
        fig1, axs = plt.subplots(1, 2, figsize=(12,3))
        x_pos1 = [2*i for i, _ in enumerate(x_fire_count)]
        years = list(x_fire_count)
        axs[0].bar(x_pos1, y_fire_count, color='#003865', align='center', tick_label=years)
        axs[0].set_alpha(0.8)
        add_value_labels(axs[0], decimal=False)
        average1 = np.mean(y_fire_count[0:-1])
        average_txt1 = "{:.1f}".format(average1)
        avg1 = axs[0].axhline(y=average1, color='#c80b2e',ls='--',linewidth=1.0)
        avg1.set_label(r"$\mu$={}".format(average_txt1))
        axs[0].set_ylabel("Fire Count (to-date)", fontsize=10)
        axs[0].set_xlabel("Year", fontsize=14)
        legend1 = axs[0].legend(frameon=False, loc='upper left')
        plt.setp(axs[0].get_legend().get_texts(), fontsize='8')
        plt.setp(axs[0].get_xticklabels(), rotation=45)

        log("---acres burned chart")
        axs[1].bar(x_pos1, y_acres_burned, color='#003865', align='center', tick_label=years)
        axs[1].set_alpha(0.8)
        add_value_labels(axs[1], decimal=True)
        average2 = np.mean(y_acres_burned[0:-1])
        average_txt2 = "{:.1f}".format(average2)
        avg2 = axs[1].axhline(y=average2, color='#c80b2e',ls='--', linewidth=1.0)
        avg2.set_label(r"$\mu$={}".format(average_txt2))
        axs[1].set_ylabel("Acres Burned (to-date)", fontsize=10)
        axs[1].set_xlabel("Year", fontsize=14)
        legend2 = axs[1].legend(frameon=False, loc='upper left')
        plt.setp(axs[1].get_legend().get_texts(), fontsize='8')
        plt.setp(axs[1].get_xticklabels(), rotation=45)

        log("generating chart for both")
        vals_to_date_plot = os.path.join(out_dir, "vals_to_date_plot_{}.png".format(PDF_TIMESTAMP))
        fig1.tight_layout()
        fig1.savefig(vals_to_date_plot, dpi=600, bbox_inches='tight')
        
        # step 5) export map as PNG
        log("copying mxd, creating output fire point map")
        mxd_copy = os.path.join(out_dir, "fire_points_map_{}.mxd".format(PDF_TIMESTAMP))
        shutil.copy(FIRE_POINTS_MXD_PATH, mxd_copy)
        mxd = arcpy.mapping.MapDocument(mxd_copy)
        out_map_png = os.path.join(out_dir, "fire_points_map_{}.png".format(PDF_TIMESTAMP))
        last_report_dt_query = set_last_report_date_query() + "AND (PROTECTION_TYPE <> 'DNR Assist Other Agency' OR PROTECTION_TYPE IS NULL) AND FIREEVNT_CLASS_LABEL_NM = 'Classified'"
        # update definition query
        m_df = arcpy.mapping.ListDataFrames(mxd)[0]  # grab the first dataframe
        l = arcpy.mapping.ListLayers(m_df)
        for layer in l:
            if layer.name == "CURRENT_FIRES":
                layer.definitionQuery = last_report_dt_query
                break
        mxd.save()
        arcpy.mapping.ExportToPNG(mxd, out_map_png, data_frame="PAGE_LAYOUT", resolution=600)
        del mxd
        log(arcpy.GetMessages())
        


        # step 5) export report
        log("exporting HTML report")
        env = Environment(loader=FileSystemLoader(r"\\dnr\divisions\rp_gis\projects\wildfire_intel_report_automation\templates"))
        template = env.get_template("eirs_intel_report_v3.html")
        template_vars = {"title": "Fire Statistics",
                            "response_pivot_table": clean_pandas_table_html(tbl_response_stats.to_html()),
                            "dnr_pivot_table": clean_pandas_table_html(tbl_dnr_stats.to_html()),
                            "causes_pivot_table": clean_pandas_table_html(tbl_dnr_causes.to_html()),
                            "time_of_report": REPORT_DATE,
                            "time_of_report_short": REPORT_DATE_SHORT,
                            "footer_time_of_report": time.ctime(),
                            "cause_labels": cause_labels,
                            "cause_vals": cause_vals,
                            "causes_plot_path": out_causes_plot,
                            "vals_to_date_plot_path": vals_to_date_plot,
                            "fire_points_png": out_map_png}
        
        html_out = template.render(template_vars)
        html_output_file = os.path.join(out_dir, "eirs_report_{}.html".format(PDF_TIMESTAMP))
        with open(html_output_file, 'w') as html_file:
            html_file.write(str.encode(str(html_out)))
            html_file.flush()
            html_file.close()

        out_pdf = os.path.join(run_dir, "eirs_report_{}.pdf".format(PDF_TIMESTAMP))
        # out_pdf_b = os.path.join(run_dir, "eirs_report_{}.pdf".format(PDF_TIMESTAMP))

        cpdf = ChromePDF(CHROME_INSTALL_DIR)
        with open(out_pdf, 'w') as out_file:
            if cpdf.html_to_pdf(html_output_file, out_file):
                log("pdf output successful")
            else:
                log("pdf output failed")
        # pdfkit.from_string(html_out, out_pdf_b, options=PDFKIT_OPTIONS)
        
        log("script completed")
        log("sending email")
        send_email("kirk.davis@dnr.wa.gov", 
                    ['kirk.davis@dnr.wa.gov', 'sarah.krock@dnr.wa.gov', 'angie.lane@dnr.wa.gov'], 
                    "Wildfire Intel Report for {}".format(PDF_TIMESTAMP), 
                    "Hello,\n\n The Wildfire Intel Automation Report ran successfully at {}. \n\nYou'll find the report attached to this email. Runtime docs can be found here: {}\n\n See you next time,\nThe Intel Report Robot  ;)".format(time.ctime(), run_dir),
                    [out_pdf])

    except Exception as e:
        log("Exception hit!: {}".format(e))
        traceback.print_exc(file=LOG_FILE); LOG_FILE.flush()
        traceback.print_exc()
        send_email("kirk.davis@dnr.wa.gov", 
                    ["kirk.davis@dnr.wa.gov", "sarah.krock@dnr.wa.gov"], 
                    "[FAIL] Wildfire Intel Report for {}".format(PDF_TIMESTAMP), 
                    "Script failed at {} - see attached log file report...".format(time.ctime()),
                    [os.path.join(run_dir, "runtime_log.txt")])
    finally:
        log("script closing")
        LOG_FILE.flush()
        LOG_FILE.close()
        arcpy.CheckInExtension("Spatial")
# end of script