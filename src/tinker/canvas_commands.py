from matplotlib.widgets import SpanSelector

def make_on_select_x(current_ax, canvas):
    """
    Selects a x-axis range in a plot.
    """
    def onselect_x(xmin, xmax): 
        if abs(xmax - xmin) < 1e-4: 
            return
        current_ax.set_xlim(xmin, xmax)
        onselect_x.selector.set_visible(False)
        canvas.draw_idle()
    return onselect_x 

# Create the reset action
def reset_x_axis_to_original(canvas, x_max_lim):
    def reset_on_right_click(event):
        # event.button == 3 represents the standard right-click mouse button
        # event.inaxes verifies the mouse is hovering inside a plot boundary
        if event.button == 3 and event.inaxes is not None:
            current_ax = event.inaxes
            current_ax.set_xlim(0,x_max_lim)
            # Reset the limits back to the original data bounds
            current_ax.relim()
            current_ax.autoscale_view()
            
            # Redraw the screen layout instantly
            canvas.draw_idle()
    return reset_on_right_click

def zoom_x_axis(fig, ax, canvas):
    fig.selectors = [] 
    shape = ax.shape
    # Figure has only one row or column
    if len(shape)==1: 
        for i in range(0,shape[0]): 
            callback = make_on_select_x(ax[i], canvas)
            span_x = SpanSelector(
                ax[i], callback, 'horizontal', interactive = True, 
                useblit = True, props=dict(alpha=0.5, facecolor='green'),
                button = 1 #<--- left click 
            )
            callback.selector = span_x 
            fig.selectors.append(span_x)   
    # Figure is two dimensional        
    if len(shape)==2: 
        for i in range(shape[0]): 
            for j in range(shape[1]): 
                callback = make_on_select_x(ax[i,j], canvas)
                span_x = SpanSelector(
                    ax[i,j], callback, 'horizontal', interactive = True, 
                    useblit = True, props = dict(alpha=0.5, facecolor='green'),
                    button = 1 #<--- left click mouse 
                )
                callback.selector = span_x 
                fig.selectors.append(span_x)

def check_pos(ax, row, col):
    """
        Function that finds the position i and j from ax[i,j].
    """
    spec = ax.get_subplotspec()
    return spec.rowspan.start == row and spec.colspan.start == col