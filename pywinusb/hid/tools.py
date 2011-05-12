import usage_pages
from helpers import HIDError
from winapi import HidP_Input, HidP_Output, HidP_Feature

def write_documentation(self, output_file):
    "Issue documentation report on output_file file like object"
    if not self.is_opened():
        raise HIDError("Device has to be opened to get documentation")
    #format
    class CompundVarDict(object):
        def __init__(self, parent):
            self.parent = parent
        def __getitem__(self, key):
            if '.' not in key:
                return self.parent[key]
            else:
                all_keys = key.split('.')
                curr_var = self.parent[all_keys[0]]
                for item in all_keys[1:]:
                    new_var = getattr(curr_var, item)
                    curr_var = new_var
                return new_var
    dev_vars = vars(self)
    dev_vars['main_usage_str'] = repr(
            usage_pages.HidUsage(self.hid_caps.usage_page, self.hid_caps.usage) )
    output_file.write( """\
HID device documentation report
===============================

Top Level Details
-----------------

Manufacturer String:    %(vendor_name)s
Product Sting:          %(product_name)s
Serial Number:          %(serial_number)s

Vendor ID:              0x%(vendor_id)04x
Product ID:             0x%(product_id)04x
Version number:         0x%(version_number)04x

Device Path:            %(device_path)s
Device Instance Id:     %(instance_id)s
Parent Instance Id:     %(parent_instance_id)s

Top level usage:        Page=0x%(hid_caps.usage_page)04x, Usage=0x%(hid_caps.usage)02x
Usage identification:   %(main_usage_str)s
Link collections:       %(hid_caps.number_link_collection_nodes)d collection(s)

Reports
-------

Input Report
~~~~~~~~~~~~
Length:     %(hid_caps.input_report_byte_length)d byte(s)
Buttons:    %(hid_caps.number_input_button_caps)d button(s)
Values:     %(hid_caps.number_input_value_caps)d value(s)

Output Report
~~~~~~~~~~~~~
length:     %(hid_caps.output_report_byte_length)d byte(s)
Buttons:    %(hid_caps.number_output_button_caps)d button(s)
Values:     %(hid_caps.number_output_value_caps)d value(s)

Feature Report
~~~~~~~~~~~~~
Length:     %(hid_caps.feature_report_byte_length)d byte(s)
Buttons:    %(hid_caps.number_feature_button_caps)d button(s)
Values:     %(hid_caps.number_feature_value_caps)d value(s)

""" % CompundVarDict(dev_vars)) #better than vars()!
    #return
    # inspect caps
    for report_kind in [HidP_Input, HidP_Output, HidP_Feature]:
        all_usages = self.usages_storage.get(report_kind, [])
        if all_usages:
            print '*** %s Caps ***' % {HidP_Input:"Input", HidP_Output:"Output", HidP_Feature:"Feature"}[report_kind]
            for usage_item in all_usages:
                print usage_item.inspect()
