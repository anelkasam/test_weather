import mpld3
import seaborn as sns
from matplotlib import pyplot as plt


def plot_forecast(data: list):
    """
    Create plots for the given data
    """
    if not data:
        return ''
    fig, ax = plt.subplots(1, 3, figsize=(15, 5))
    fig_manager = plt.get_current_fig_manager()
    if hasattr(fig_manager, 'window'):
        fig_manager.window.showMaximized()
    sns.set(style="darkgrid")

    temp = sns.lineplot(x=[f.data_time for f in data], y=[f.temperature for f in data], ax=ax[0])
    temp.set_title('Temperature dependency')
    temp.set_xlabel('date')
    temp.set_ylabel('temp')

    pressure = sns.lineplot(x=[f.data_time for f in data], y=[f.pressure for f in data], ax=ax[1])
    pressure.set_title('Pressure dependency')
    pressure.set_xlabel('date')
    pressure.set_ylabel('pressure')

    wind = sns.lineplot(x=[f.data_time for f in data], y=[f.windSpeed for f in data], ax=ax[2])
    wind.set_title('Wind speed dependency')
    wind.set_xlabel('date')
    wind.set_ylabel(' speedwind')

    return mpld3.fig_to_html(fig)
