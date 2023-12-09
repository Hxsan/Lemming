from django import template
register = template.Library()


@register.filter
def format(value):
    formatted_time = ''
    # Splits time into days / hours / minutes / seconds
    if value != None and value != 0:
        days, rem1 = divmod(value, 86400)
        hours, rem2 = divmod(rem1, 3600)
        minutes, seconds = divmod(rem2, 60)
        if days:
            formatted_time += f"{days}d "
        if hours:
            formatted_time += f"{hours}h "
        if minutes:
            formatted_time += f"{minutes}m "
        if seconds:
            formatted_time += f"{seconds}s "
        return formatted_time
    else:
        return "No time has been spent."


