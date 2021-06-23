Instructions to create a iCOMOX_GUI version 2.5.7 application with IOTC support.

In the PyCharm:
1. Create new project with its own Python virtual environmet
2. Update the pip and setuptools to the latest versions
3. Install the following packages:
Pillow, tk-tools, pyserial, numpy, matplotlib, scipy, iotc, requests, openpyxl, pywin32
4. Update any installed package whosoe version is not the recent one (PyCharm shows it and allows one to update to the latest version)
5. In client.py (one of the libraries files) comment the following lines:
        # Prevent CVE-2019-9740.
         match = _contains_disallowed_url_pchar_re.search(url)
         if match:
             raise InvalidURL(f"URL can't contain control characters. {url!r} "
                              f"(found at least {match.group()!r})")
they begins in line 1115. Without it, the IOTC connect() fails.
6. Prepare a replacment to the file IOT_Shiratech.py: this file contains a list of the supported iCOMOX unique IDs, and a function
uniqueID_to_IotcInfo(uniqueID), which gets the uniqueID of the iCOMOX (bytearray of 16 bytes), and returns a list that contains scopeID, deviceID, primaryKey & SecondaryKey.
7. In IOT_Connectivity.py replace the import from IOT_Shiratech to the import of the data from your file

