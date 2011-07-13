from django.shortcuts import get_object_or_404, render_to_response
from django.http import HttpResponseRedirect, HttpResponse
from regr.models import *
from converttocsv import StatusTotals
from django.db.models import Count
# for the pie chart generation
from pyofc2  import * 
import random
import time

# Create your views here.
def welcome(request):
    #return HttpResponse("welcome")
    return render_to_response('index.html')

def winapproach(request):
    return HttpResponse("winapproach")

def code_paths(request):
    return HttpResponse("code paths")

def regression(request):
    return HttpResponse("regression")

def links(request):
    return HttpResponse("links")

# Lists all entered projects ie FM/CM
def list_projects(request):
    project_list = CodeBase.objects.all()
    return render_to_response('listprojects.html', {'project_list': project_list})
    
# Lists all branches for the selected project ie DEV/PROD
def list_branches(request, project):
    project_list = CodeBase.objects.filter(project__exact=project)
    return render_to_response('listprojects.html', {'project_list': project_list})

# Lists all releases for the selected branch ie 24-0-219 etc
def list_releases(request, project, branch):
    selected_project = CodeBase.objects.get(project__exact=project, branch__exact=branch)
    # todo should we return 404 here?
    release_list = selected_project.release_set.values()
    return render_to_response('listreleases.html', {'release_list': release_list, 'project':selected_project})

# Displays the release figures totals chart
def display_totals_chart(request, project, branch):
    selected_project = CodeBase.objects.get(project__exact=project, branch__exact=branch)
    return render_to_response('displaychart.html', {'chart_type': "bar", 'project':selected_project})
    
# Displays the release pass rate chart
def display_pass_rate_chart(request, project, branch):
    selected_project = CodeBase.objects.get(project__exact=project, branch__exact=branch)
    return render_to_response('displaychart.html', {'chart_type': "line", 'project':selected_project})
    
# Displays the details for the given scenario file
def display_file_details(request, project, branch, release, package, layer, directory, filename):
    selected_project = CodeBase.objects.get(project__exact=project, branch__exact=branch)
    return render_to_response('listfiledetails.html', {'project' : selected_project, \
                                                       'release' : release, \
                                                       'package' : package, \
                                                       'layer' : layer, \
                                                       'directory' : directory, \
                                                       'filename' : filename, \
                                                       'logname' : filename.replace('.scn', '.log'), \
                                                       'diffname' : filename.replace('.scn', '.diff')})

# Gets the regression pass status for the selected file over all the releases.
def display_file_history(request, project, branch, release, package, layer, directory, filename):
    selected_project = CodeBase.objects.get(project__exact=project, branch__exact=branch)
    
    historical_status_list = RegressionResult.objects.filter(release__code_base__id__exact=selected_project.id, file__package__exact=package, file__layer__exact=layer, file__directory_path__exact=directory, file__file_name__exact=filename).values('release__name', 'status')
    stats_class = StatusTotals()
    processed_list = []
    for stat_item in historical_status_list:
        new_hash = {}
        new_hash['release_name'] = str(stat_item['release__name'])
        new_hash['status'] = stats_class.getStatusStr(stat_item['status'])
        processed_list.append(new_hash)
    
    return render_to_response('listfilehistory.html', {'project' : selected_project, \
                                                       'release' : release, \
                                                       'package' : package, \
                                                       'layer' : layer, \
                                                       'directory' : directory, \
                                                       'filename' : filename, \
                                                       'historical_status_list':processed_list})
    

def display_results(request, project, branch, release, package='all', layer='all', directory='all'):
    selected_project = CodeBase.objects.get(project__exact=project, branch__exact=branch)
    # todo should we return 404 here?
    selected_release = selected_project.release_set.get(name__exact=release)
    # list of packages for the release
    packages_hash = selected_release.files.values('package').order_by('package').distinct()
    packages_list = [str(x.get('package')) for x in packages_hash]
    
    # get the list of dirs for the package
    dirs_hash = None
    release_stats = {}
    if package != 'all':
        if layer != 'all':
            dirs_hash = selected_release.files.filter(package__exact=package, layer__exact=layer).values('layer', 'directory_path').order_by('layer').order_by('directory_path').distinct()
        else:
            dirs_hash = selected_release.files.filter(package__exact=package).values('layer', 'directory_path').order_by('directory_path').distinct()
        #dirs_list = [(str(x.get('layer')), str(x.get('directory_path'))) for x in dirs_hash]
    else:
        # Get top level stats for the release.
        stats = RegressionResult.objects.filter(release__id__exact=1).values('status').annotate(Count('status')).order_by('status')
        total_cases = 0
        pass_cases = 0
        fail_cases = 0
        for stat_item in stats:
            total_cases = total_cases + stat_item['status__count']
            release_stats[stat_item['status']] = str(stat_item['status__count'])
            if stat_item['status'] == 0:
                pass_cases = int(stat_item['status__count'])
            elif stat_item['status'] == 1:
                fail_cases = int(stat_item['status__count'])
        release_stats[5] = total_cases
        # Remember that the pass rate should include pass, void and new, and not just pass!
        release_stats[6] = round((float(total_cases - fail_cases) / total_cases) * 100, 2)
        
    # get the list of files for the directory
    files_list = None
    print "value of dir is: %s\n" % directory
    #template_file = 'listresults.html'
    template_file = 'listfiles.html'
    if directory != 'all':
        
        if layer != 'all':
            files_list = RegressionResult.objects.filter(file__package__exact=package, file__directory_path__exact=directory, release__id__exact=selected_release.id)
        else:
            files_list = RegressionResult.objects.filter(file__package__exact=package, file__layer__exact=layer, file__directory_path__exact=directory, release__id__exact=selected_release.id)
        print "number of files found: %d " % len(files_list)
        
    
    return render_to_response(template_file, {'package_list' : packages_list, \
                                                              'project' : selected_project, \
                                                              'release' : selected_release, \
                                                              'package' : package, \
                                                              'layer' : layer, \
                                                              'directory' : directory, \
                                                              'dirs_hash' : dirs_hash, \
                                                              'files_list' : files_list, \
                                                              'release_stats' : release_stats})

def chart_data2(request, type='bar'):
    # Display the failures across the packages for the given release
    chart = open_flash_chart()
    t = title(text="FM Package Failures")
    chart.title = t

    b1 = bar()
    b1.text="Failures"
    
    # todo update for specified release
    results = RegressionResult.objects.filter(status='1', release__id__exact=1).values('file__package').annotate(Count('file__package')).order_by('file__package')
    package_names = []
    package_failures = []
    for result_item in results:
        package_names.append(result_item['file__package'])
        package_failures.append(result_item['file__package__count'])
    b1.values = package_failures
    
    chart.add_element(b1)
    chart.y_axis = y_axis(min=0, max=250, steps=10)
    chart.x_axis = x_axis(labels=labels(labels=package_names))
    return HttpResponse(chart.render())

def chart_data(request, type='bar'):
    t = title(text=time.strftime('%a %Y %b %d'))
    #tt = tooltip("P #val#%")
    chart = open_flash_chart()
    chart.title = t    

    # Generic bar chart
    if type == 'bar1':
        b1 = bar()
        b1.values = range(9,0,-1)
        b2 = bar()
        b2.values = [random.randint(0,9) for i in range(9)]
        b2.colour = '#56acde'
        chart.add_element(b1)
        chart.add_element(b2)
        
    # Display the release stats for all releases - bar chart which shows three bars per release
    if type == 'bar':
        t = title(text="FM Release Figures")
        chart.title = t
        release_list = Release.objects.all()
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
        chart.x_axis = x_axis(labels=labels(labels=release_names))
    # Generic line chart
    elif type == 'line':
        t = title(text="FM Pass Rate")
        chart.title = t
        release_list = Release.objects.all()
        l1 = line()
        #l1.text="total"
        
        release_names = []
        percentage_pass = []
        for rel in release_list:
            release_names.append(str(rel.name))
            if rel.total_files == 0:
                pass_rate = 0
            else:
                pass_rate = round((float(rel.total_files - rel.total_fail) / rel.total_files) * 100, 2)
            percentage_pass.append(pass_rate)
        
        l1.values = percentage_pass
        #l1.values = [9,8,7,6,5.0,4,3.2,2,1]
        chart.add_element(l1)
        chart.y_axis = y_axis(min=0, max=100, steps=10)
        chart.x_axis = x_axis(labels=labels(labels=release_names))
        
    # Line chart showing the percentage pass rate across releases
    elif type == 'line1':
        l = line()
        l.values = [9,8,7,6,5.0,4,3.2,2,1]
        chart.add_element(l)
    # Generic pie chart
    elif type == 'pie1':
        p1 = pie();
        pa = pie_value(value=1, label='a', colour='#FF0000');
        pb = pie_value(value=2, label='b', colour='#F0DD00');
        pc = pie_value(value=3, label='c', colour='#FFDD00');
        p1.values = [pa, pb, pc]
        #p1.labels = ['a', 'b', 'c', 'd']
        chart.add_element(p1)
    # Pie chart for specific release which shows break down of file types: pass, fail, void, new etc
    elif type == 'pie':
        colour_mapping = {
            0 : '#00FF00', \
            1 : '#FF0000', \
            2 : '#FFDD00', \
            3 : '#0000FF', \
            4 : '#0D0D0D' \
        }
        # Obtain stats for release
        # todo need to dynamically select the release
        stats = RegressionResult.objects.filter(release__id__exact=1).values('status').annotate(Count('status')).order_by('status')
        # Reformat data
        release_stats = {}
        for stat_item in stats:
            release_stats[int(stat_item['status'])] = int(stat_item['status__count'])
        # Set data for pie chart    
        p1 = pie();
        data_array = []
        stats_class = StatusTotals()
        for case_type in release_stats:
            #print "BSK %d %d %s %s" %(g, release_stats[g], stat_class.getStatusStr(g), colour_mapping[g])
            #current_pie_data = pie_value(value=int(release_stats[case_type]), label=stats_class.getStatusStr(case_type), colour=colour_mapping[case_type])
            current_pie_data = pie_value(value=release_stats[case_type], label=stats_class.getStatusStr(case_type), colour=colour_mapping[case_type])
            data_array.append(current_pie_data)
        p1.values = data_array
        
        chart.add_element(p1)
    return HttpResponse(chart.render())
