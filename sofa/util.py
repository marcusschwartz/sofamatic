"""some sofa utilities"""


def merge_status_details(details_set):
    output = {}
    for set_name, details in details_set.items():
        for detail_name, detail_value in details.items():
            output["%s.%s" % (set_name, detail_name)] = detail_value
    return output


class Status(object):
    pass
