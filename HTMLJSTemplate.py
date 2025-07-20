import json

def generate_html_with_js(plotly_div):
    js_code = """
        <script src=\"qrc:///qtwebchannel/qwebchannel.js\"></script>
        <script>
        new QWebChannel(qt.webChannelTransport, function(channel) {
            window.handler = channel.objects.handler;
            var plot = document.getElementsByClassName('plotly-graph-div')[0];
            plot.on('plotly_click', function(data){
                var point = data.points[0];
                var clicked_data = {
                    id: point.id,
                    label: point.label,
                    value: point.value,
                    last_ring: point.customdata && point.customdata.length > 0 ? point.customdata[0] : false,
                    compte_id: point.customdata && point.customdata.length > 1 ? point.customdata[1] : null,
                    tiers_id: point.customdata && point.customdata.length > 1 ? point.customdata[2] : null
                };
                handler.handle_click(JSON.stringify(clicked_data));
            });
        });
        </script>
    """
    html_content = f"""
    <html>
    <head>
    <meta charset=\"utf-8\">
    </head>
    <body>
    <div style=\"display: flex; justify-content: center; align-items: center; width: 100%; height: 100%;\">
    {plotly_div}
    </div>
    {js_code}
    </body>
    </html>
    """
    return html_content
