import re
import os
import sys
from subprocess import call, Popen, PIPE

def _cmd(command, args):
    args = 'rrdtool %s %s' % (command, args)

    p = Popen([args], shell=True, stdin=PIPE, stdout=PIPE, close_fds=True)
    stdout, stderr = (p.stdout, p.stderr)
    err = output = None
    try:
        err = stderr.read()
    except:
        output = stdout.read()
    if err:
        raise Exception, err
    else:
        return output

def create(filename, parameters):
    '''
    >>> filename = '/tmp/test.rrd'
    >>> parameters = ' --start 920804400'
    >>> parameters += ' DS:speed:COUNTER:600:U:U'
    >>> parameters += ' RRA:AVERAGE:0.5:1:24'
    >>> parameters += ' RRA:AVERAGE:0.5:6:10'
    >>> create(filename, parameters)
    >>> os.path.exists(filename)
    True

    >>> os.unlink(filename)
    >>> os.path.exists(filename)
    False
    '''
    parameters = '%s %s' % (filename, parameters)
    output = _cmd('create', parameters)

def update(filename, data):
    '''
    >>> filename = '/tmp/test.rrd'
    >>> parameters = ' --start 920804400'
    >>> parameters += ' DS:speed:COUNTER:600:U:U'
    >>> parameters += ' RRA:AVERAGE:0.5:1:24'
    >>> parameters += ' RRA:AVERAGE:0.5:6:10'
    >>> create(filename, parameters)
    >>> os.path.exists(filename)
    True

    >>> update('/tmp/test.rrd', '920804700:12345 920805000:12357 920805300:12363')
    >>> update('/tmp/test.rrd', '920805600:12363 920805900:12363 920806200:12373')
    >>> update('/tmp/test.rrd', '920806500:12383 920806800:12393 920807100:12399')
    >>> update('/tmp/test.rrd', '920807400:12405 920807700:12411 920808000:12415')
    >>> update('/tmp/test.rrd', '920808300:12420 920808600:12422 920808900:12423')

    >>> os.unlink(filename)
    >>> os.path.exists(filename)
    False
    '''
    parameters = '%s %s' % (filename, data)
    output = _cmd('update', parameters)

def fetchRaw(filename, query):
    parameters = '%s %s' % (filename, query)
    return _cmd('fetch', parameters).strip()

def fetch(filename, query, results_as_generator=True):
    '''
    >>> filename = '/tmp/test.rrd'
    >>> parameters = ' --start 920804400'
    >>> parameters += ' DS:speed:COUNTER:600:U:U'
    >>> parameters += ' RRA:AVERAGE:0.5:1:24'
    >>> parameters += ' RRA:AVERAGE:0.5:6:10'
    >>> create(filename, parameters)
    >>> os.path.exists(filename)
    True

    >>> update('/tmp/test.rrd', '920804700:12345 920805000:12357 920805300:12363')
    >>> update('/tmp/test.rrd', '920805600:12363 920805900:12363 920806200:12373')
    >>> update('/tmp/test.rrd', '920806500:12383 920806800:12393 920807100:12399')
    >>> update('/tmp/test.rrd', '920807400:12405 920807700:12411 920808000:12415')
    >>> update('/tmp/test.rrd', '920808300:12420 920808600:12422 920808900:12423')

    >>> ds_name, results = fetch('/tmp/test.rrd', 'AVERAGE --start 920804400 --end 920809200')
    >>> ds_name
    'speed'
    >>> results.next()
    (920804700, None)
    >>> ds_name, results = fetch('/tmp/test.rrd', 'AVERAGE --start 920804400 --end 920809200',
    ...   results_as_generator=False)
    >>> len(results)
    16

    >>> os.unlink(filename)
    >>> os.path.exists(filename)
    False
    '''
    output = fetchRaw(filename, query)
    lines = output.split('\n')
    ds_name = lines[0]
    # lines[1] is blank
    results = generateResultLines(lines[2:])
    if results_as_generator:
        return (ds_name, results)
    else:
        return (ds_name, list(results))

def generateResultLines(lines):
    for line in lines:
        line = line.strip()
        time, value = re.split(':\s+', line)
        value = value.strip()
        if value.lower() in ['nan', 'unkn', 'u']:
            value = None
        else:
            value = float(value)
        yield (int(time.strip()), value)

def graph(filename, parameters):
    '''
    >>> filename = '/tmp/speed.png'
    >>> rrdfile = '/tmp/test.rrd'
    >>> parameters = ' --start 920804400'
    >>> parameters += ' DS:speed:COUNTER:600:U:U'
    >>> parameters += ' RRA:AVERAGE:0.5:1:24'
    >>> parameters += ' RRA:AVERAGE:0.5:6:10'
    >>> create(rrdfile, parameters)
    >>> os.path.exists(rrdfile)
    True

    >>> update('/tmp/test.rrd', '920804700:12345 920805000:12357 920805300:12363')
    >>> update('/tmp/test.rrd', '920805600:12363 920805900:12363 920806200:12373')
    >>> update('/tmp/test.rrd', '920806500:12383 920806800:12393 920807100:12399')
    >>> update('/tmp/test.rrd', '920807400:12405 920807700:12411 920808000:12415')
    >>> update('/tmp/test.rrd', '920808300:12420 920808600:12422 920808900:12423')

    >>> parameters = ' --start 920804400 --end 920808000'
    >>> parameters += ' --vertical-label km/h'
    >>> parameters += ' DEF:myspeed=%s:speed:AVERAGE' % rrdfile
    >>> parameters += ' CDEF:realspeed=myspeed,1000,*'
    >>> parameters += ' CDEF:kmh=myspeed,3600,*'
    >>> parameters += ' CDEF:fast=kmh,100,GT,kmh,0,IF'
    >>> parameters += ' CDEF:good=kmh,100,GT,0,kmh,IF'
    >>> parameters += ' HRULE:100#0000FF:"Maximum allowed"'
    >>> parameters += ' AREA:good#00FF00:"Good speed"'
    >>> parameters += ' AREA:fast#00FFFF:"Too fast"'
    >>> parameters += ' LINE2:realspeed#FF0000:Unadjusted'
    >>> if os.path.exists(filename):
    ...   os.unlink(filename)
    >>> graph(filename, parameters)
    >>> os.path.exists(filename)
    True

    >>> os.unlink(rrdfile)
    >>> os.path.exists(rrdfile)
    False
    '''
    parameters = '%s %s' % (filename, parameters)
    _cmd('graph', parameters)

def buildParameters(obj, valid_list):
    param_template = ' --%s %s'
    params = ''
    for param in valid_list:
        attr = getattr(obj, param)
        if attr:
            param = param.replace('_', '-')
            params += param_template % (param, attr)
    return params.strip()
        
def prepareObject(function, obj):
    '''
    This is a funtion that serves to make interacting with the
    backend as transparent as possible. It's sole purpose it to
    prepare the attributes and data of the various pyrrd objects
    for use by the functions that call out to rrdtool.

    For all of the rrdtool-methods in this module, we need a filename
    and then parameters -- both as strings. That's it.

    This function will get called by methods in the pyrrd wrapper
    objects. For instance, most of the methods of pyrrd.rrd.RRD
    will call this function. In graph, Pretty much only the method 
    pyrrd.graph.Graph.write() will call this function.
    '''
    if function == 'create':
        valid_params = ['start']
        params = buildParameters(obj, valid_params)
        data = ' '.join([ str(x) for x in obj.ds ])
        data += ' ' + ' '.join([ str(x) for x in obj.rra ])
        return (obj.filename, "%s %s" % (params, data))
    if function == 'update':
        params = ' '.join([ '%s:%s' % (time, values) 
            for time, values in obj.values ])
        return (obj.filename, params)
    if function == 'fetch':
        pass
    if function == 'graph':
        valid_params = ['start', 'end', 'step', 'title',
            'vertical_label', 'width', 'height', 'only_graph',
            'upper_limit', 'lower_limit', 'rigid', 'alt_autoscale',
            'alt_autoscale_max', 'no_gridfit', 'x_grid', 'y_grid',
            'alt_y_grid', 'logarithmic', 'units_exponent', 'zoom',
            'font', 'font_render_mode', 'interlaced', 'no_legend',
            'force_rules_legend', 'tabwidth', 'base', 'color']
        
        params = buildParameters(obj, valid_params)
        data = ' '.join([ str(x) for x in obj.data ])
        return (obj.filename, "%s %s" % (params, data))

def _test():
    import doctest, external
    return doctest.testmod(external)

if __name__ == '__main__':
    _test()
