# **wildfire-intel-report-automation** 🔥

------

An Wildfire Intel HTML-to-PDF report creation pipeline based on data from the WA DNR Emergency Incident Reporting System - Fire Statistics ArcGIS Point Feature Service: https://gis.dnr.wa.gov/site3/rest/services/Public_Wildfire/WADNR_PUBLIC_WD_WildFire_Data/MapServer/2

Built using *Python*, *arcpy*, *Headless Chrome*, *pandas*, *matplotlib*, *jinja2*, *requests*, and *HTML/CSS*.  Deployed as an automated task which runs at 6am on DNR Servers.  These Intel Reports are pushed to our Intel Dashboard during wildfire season.

[See an example of the output report here](https://github.com/kirk5davis/wildfire-intel-automation/blob/master/docs/example_output/20200623_084926_wildfire_intel_automation/eirs_report_20200623_0800.pdf)