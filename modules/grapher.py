import altair as alt
import streamlit as st

class GraphDF:
    """"
    Graph data in standard format
    """
    def __init__(self):
        pass

    # Return a dataframe
    @st.experimental_memo(ttl=600)
    def bar_chart(_self, df, x, y, tooltip_1=None, tooltip_2=None, tooltip_3=None, x_format=',', tooltip1_format=',', tooltip2_format=',', tooltip3_format=',', x_labelFontSize=20):
        if tooltip_1 == None:
            tooltip=[y, alt.Tooltip(x, format=x_format)]
        elif tooltip_2 == None:
            tooltip=[y, alt.Tooltip(x, format=x_format), alt.Tooltip(tooltip_1, format=tooltip1_format)]
        elif tooltip_3 == None:
            tooltip=[y, alt.Tooltip(x, format=x_format), alt.Tooltip(tooltip_1, format=tooltip1_format), alt.Tooltip(tooltip_2, format=tooltip2_format)]
        else:
            tooltip=[y, alt.Tooltip(x, format=x_format), alt.Tooltip(tooltip_1, format=tooltip1_format), alt.Tooltip(tooltip_2, format=tooltip2_format), alt.Tooltip(tooltip_3, format=tooltip3_format)]

        bars = alt.Chart(df, height=alt.Step(30) # adjust the spacing of the bars
        ).mark_bar(
            cornerRadiusBottomRight=5,
            cornerRadiusTopRight=5    
        ).encode(
            y=alt.Y(y, sort=None, title="", axis=alt.Axis(labelFontSize=x_labelFontSize) ), # , labelAngle=-35
            x=alt.X(x, axis=None), 
            color=alt.Color(x, legend=None, scale=alt.Scale(scheme='darkmulti')), # https://vega.github.io/vega/docs/schemes/
            tooltip=tooltip
        )

        text = bars.mark_text(
            align='left',
            baseline='middle',
            color='white',
            dx=3, 
            fontSize=20
        ).encode(
            text=alt.Text(x, format=x_format)
        )

        final_chart = alt.layer(bars, text
        ).configure_view(
            strokeWidth=0
        ).configure_scale(
            bandPaddingInner=0.2 # adjust the width of the bars
        ).configure_axis(
            grid=False
        )
        return final_chart