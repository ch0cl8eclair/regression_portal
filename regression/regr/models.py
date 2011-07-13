from django.db import models


# Create your models here.
class CodeBase(models.Model):
    project = models.CharField(max_length=5)
    branch = models.CharField(max_length=20)

    def __unicode__(self):
        return "%s, %s" % (self.project, self.branch)
    
class Release(models.Model):
    code_base = models.ForeignKey(CodeBase)
    files = models.ManyToManyField('RegressionFile', through='RegressionResult')
    name = models.CharField(max_length=12)
    date = models.DateTimeField()
    # Define stats counters
    total_files = models.PositiveIntegerField()
    total_pass  = models.PositiveIntegerField()
    total_fail  = models.PositiveIntegerField()
    total_void  = models.PositiveIntegerField()
    total_new   = models.PositiveIntegerField()
    total_other = models.PositiveIntegerField()

    class Meta:
        ordering = ['code_base', 'date', 'name']
        
    def __unicode__(self):
        return "%s, %s, %s" %(self.code_base, self.name, self.date.strftime("%d %m %y"))
        
    def initialise_counters(self):
        self.total_files = 0
        self.total_pass = 0
        self.total_fail = 0
        self.total_void = 0
        self.total_new = 0
        self.total_other = 0

class RegressionFile(models.Model):
    code_base = models.ForeignKey(CodeBase)
    package = models.CharField(max_length = 20)
    layer = models.CharField(max_length = 10)
    directory_path = models.CharField(max_length = 150)
    file_name = models.CharField(max_length = 50)

    class Meta:
        ordering = ['code_base', 'package', 'layer', 'directory_path', 'file_name']
        
    def __unicode__(self):
        return "%s, %s, %s, %s" % (self.package, self.layer, self.directory_path, self.file_name)

class RegressionResult(models.Model):
    release = models.ForeignKey(Release)
    file = models.ForeignKey(RegressionFile)
    status = models.PositiveIntegerField()
    
    verified = models.BooleanField()
    user = models.CharField(max_length=15, blank=True, null=True)
    
    diff_lines = models.CommaSeparatedIntegerField(max_length=3, blank=True, null=True)
    comment = models.CharField(max_length=50, blank=True, null=True)
    
    class Meta:
        ordering = ['release', 'file']

    def getStatusAsStr(self):
        return StatusTotals().getStatusStr(self.status)

    def __unicode__(self):
        return "%s, %s, %s" % (self.release, self.file, self.status)

###############################################################################
class StatusTotals:
    '''Used to process and hold the total regression stats for a regression run.'''

#        "OK":1,
#        "Failed":2,
#        "Void":3,
#        "New":4
#        "Other":5
# There is also dumped status, but we'll include it under other
    def __init__(self):
        self.total_count = 0
        self.total_pass = 0
        self.total_fail = 0
        self.total_void = 0
        self.total_new = 0
        self.total_other = 0
    def getTotalCount(self):
        return self.total_count
    def getTotalPass(self):
        return self.total_pass
    def getTotalFail(self):
        return self.total_fail
    def getTotalVoid(self):
        return self.total_void
    def getTotalNew(self):
        return self.total_new
    def getTotalOther(self):
        return self.total_other
    def updateTotals(self, cfStatus):
        self.total_count += 1
        if cfStatus == "OK":
            self.total_pass += 1
        elif cfStatus == "Failed":
            self.total_fail += 1
        elif cfStatus == "Void":
            self.total_void += 1
        elif cfStatus == "New":
            self.total_new += 1
        else:
            self.total_other += 1
    def getNumericValue(self, status_str):
        if status_str == "OK":
            return 0
        elif status_str == "Failed":
            return 1
        elif status_str == "Void":
            return 2
        elif status_str == "New":
            return 3
        else:
            return 4
    def getStatusStr(self, status_num):
        if status_num == 0:
            return "OK"
        elif status_num == 1:
            return "Failed"
        elif status_num == 2:
            return "Void"
        elif status_num == 3:
            return "New"
        else:
            return "Unknown"
    def __str__(self):
        return "total files: %d, pass: %d, fail: %d" % (self.total_count, self.total_pass, self.total_fail)
