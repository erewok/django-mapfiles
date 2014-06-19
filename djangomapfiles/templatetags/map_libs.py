from django import template

register = template.Library()

@register.inclusion_tag('js_map_libs.html')
def load_map_lib(requested_lib):
        map_libs = {'openlayers-js' : 'http://openlayers.org/api/OpenLayers.js',
                    'leaflet-js' : 'http://cdn.leafletjs.com/leaflet-0.7.2/leaflet.js'}
        map_styles = {'leaflet-css' : 'http://cdn.leafletjs.com/leaflet-0.7.2/leaflet.css'}

        maps = {}
        maps_css = {}
        if requested_lib == 'leaflet':
                maps['js'] = map_libs['leaflet-js']
                maps_css['css'] = map_styles['leaflet-css']
        elif requested_lib == 'openlayers':
                maps['js'] = map_libs['openlayers-js']
        else:
                errmsg = """{} library is unknown."""
                raise template.TemplateSyntaxError(errmsg.format(requested_lib)) 
        if maps_css:
                return {'maps' : maps, 'maps_css' : maps_css}
        else:
                return {'maps' : maps}
