from django import template

register = template.Library()

@register.inclusion_tag('jslibs.html')
def load_js_libs(*args):
        js_libs = {'jquery' : '//ajax.googleapis.com/ajax/libs/jquery/1.10.2/jquery.min.js',
                   'jquery-ui': '//ajax.googleapis.com/ajax/libs/jqueryui/1.10.3/jquery-ui.min.js',
                   'underscore' : '//cdnjs.cloudflare.com/ajax/libs/underscore.js/1.5.2/underscore-min.js',
                   'backbone' : '/cdnjs.cloudflare.com/ajax/libs/backbone.js/1.0.0/backbone-min.js',
                   'ember' : '//cdnjs.cloudflare.com/ajax/libs/ember.js/1.3.1/ember.min.js',
                   'angular' : '//ajax.googleapis.com/ajax/libs/angularjs/1.2.8/angular.min.js',
                   'dojo' : '//ajax.googleapis.com/ajax/libs/dojo/1.9.2/dojo/dojo.js'
        }
        loaded_libs = []
        errors = []
        for arg in args:
            if arg in js_libs:
                loaded_libs.append(js_libs[arg])
            else:
                errors.append(arg)
        
        if errors:
            errmsg = """{} library is unknown."""
            raise template.TemplateSyntaxError(errmsg.format(" ".join(errors)))
        else:
            return {'loaded_libs' : loaded_libs}
