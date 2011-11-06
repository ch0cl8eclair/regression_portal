from django.db.models import Count
from regr.models import *
from regr.utils import getReleaseTotalStats, TOTAL_KEY
from django.http import HttpResponse, Http404

import time

# for the pie chart generation
from pyofc2 import *

###############################################################################
# Chart Data Requests - used by the chart object to get the data figures
###############################################################################

def chart_data(request, type='bar', releaseID=-1):
    '''json data request handler for ofc chart data requests'''
    t = title(text=time.strftime('%a %Y %b %d'))
    #tt = tooltip("P #val#%")
    chart = open_flash_chart()
    chart.title = t

    # Display the release stats for all releases - bar chart which shows three bars per release
    if type == 'bar':
        t = title(text="FM Release Figures")
        chart.title = t
        release_list = Release.objects.all().order_by('date')[:10]
        b1 = bar()
        b1.text="total"

        b2 = bar()
        b2.colour = '#00ee00'
        b2.text="pass"

        b3 = bar()
        b3.colour = '#ee0000'
        b3.text="fail"

        total_values = []
        pass_values = []
        fail_values = []
        release_names = []
        for rel in release_list:
            total_values.append(rel.total_files)
            pass_values.append(rel.total_pass)
            fail_values.append(rel.total_fail)
            release_names.append(str(rel.name))

        b1.values = total_values
        b2.values = pass_values
        b3.values = fail_values

        chart.add_element(b1)
        chart.add_element(b2)
        chart.add_element(b3)
        chart.y_axis = y_axis(min=0, max=20000, steps=1000)
        #chart.x_axis = x_axis(labels=labels(labels=release_names))

        # Custom x axis to display vertical labels
        x = x_axis()
        xlbls = x_axis_labels(steps=1, rotate='vertical', colour='#FF0000')
        xlbls.labels = release_names
        x.labels = xlbls
        chart.x_axis = x

    # Generic line chart
    elif type == 'line':
        t = title(text="FM Pass Rate")
        chart.title = t
        release_list = Release.objects.all().order_by('date')
        l1 = line()

        release_names = []
        percentage_pass = []
        for rel in release_list:
            release_names.append(rel.getBasicDateStr())
            if rel.total_files == 0:
                pass_rate = 0
            else:
                pass_rate = round((float(rel.total_files - rel.total_fail) / rel.total_files) * 100, 2)
            percentage_pass.append(pass_rate)

        l1.values = percentage_pass
        chart.add_element(l1)
        chart.y_axis = y_axis(min=0, max=100, steps=10)
        #chart.x_axis = x_axis(labels=labels(labels=release_names))

        # Custom x axis to display vertical labels
        x = x_axis()
        stepVal=max(len(release_names)/10, 1)
        xlbls = x_axis_labels(steps=stepVal, rotate='vertical', colour='#FF0000')
        xlbls.labels = release_names
        x.labels = xlbls
        chart.x_axis = x

    # Pie chart for specific release which shows break down of file types: pass, fail, void, new etc
    elif type == 'pie':
        t = title(text="Release Breakdown")
        chart.title = t
        colour_mapping = {
            0 : '#00FF00', \
            1 : '#FF0000', \
            2 : '#FFDD00', \
            3 : '#0000FF', \
            4 : '#0D0D0D' \
        }
        # Obtain stats for release
        # todo need to dynamically select the release
        stats = RegressionResult.objects.filter(release__id__exact=releaseID).values('status').order_by('status').annotate(Count('status'))
        # Reformat data
        release_stats = {}
        for stat_item in stats:
            release_stats[int(stat_item['status'])] = int(stat_item['status__count'])
        # Set data for pie chart
        p1 = pie();
        data_array = []
        stats_class = StatusTotals()

        for case_type in release_stats.keys():
            current_pie_data = pie_value(value=release_stats[case_type], label=stats_class.getStatusStr(case_type), colour=colour_mapping[case_type])
            data_array.append(current_pie_data)
            
        if len(data_array) == 4:
            temp = data_array[1]
            data_array[1] = data_array[2]
            data_array[2] = temp

        p1.values = data_array

        chart.add_element(p1)
        
    # Bar chart to show package failures for a given release
    elif type == 'release_packages':
        release_stats = getReleaseTotalStats(releaseID)

        # Now build the chart
        t = title(text="Release Total Package stats.")
        chart.title = t

        b2 = bar()
        b2.colour = '#00ee00'
        b2.text="total"

        total_values = []
        package_names = []
        for pkg in sorted(release_stats.keys()):
            statuses = release_stats.get(pkg)
            total_values.append(statuses[TOTAL_KEY])
            package_names.append(pkg)

        b2.values = total_values

        chart.add_element(b2)

        chart.y_axis = y_axis(min=0, max=5000, steps=500)
        # Custom x axis to display vertical labels
        x = x_axis()
        xlbls = x_axis_labels(steps=1, rotate='vertical', colour='#FF0000')
        xlbls.labels = package_names
        x.labels = xlbls
        chart.x_axis = x

    elif type == 'release_packages_fail':
        release_stats = getReleaseTotalStats(releaseID)
        
        # Now build the chart
        t = title(text="Release Package Failure stats.")
        chart.title = t

        b3 = bar()
        b3.colour = '#ee0000'
        b3.text="fail"

        total_values = []
        pass_values = []
        fail_values = []
        package_names = []
        for pkg in sorted(release_stats.keys()):
            statuses = release_stats.get(pkg)
            pass_values.append(statuses.get(0, 0))
            fail_values.append(statuses.get(1, 0))
            package_names.append(pkg)

        b3.values = fail_values

        #chart.add_element(b2)
        chart.add_element(b3)
        chart.y_axis = y_axis(min=0, max=400, steps=20)
        # Custom x axis to display vertical labels
        x = x_axis()
        xlbls = x_axis_labels(steps=1, rotate='vertical', colour='#FF0000')
        xlbls.labels = package_names
        x.labels = xlbls
        chart.x_axis = x

        #chart.x_axis = x_axis(labels=labels(labels=package_names))

    return HttpResponse(chart.render())