# December 21 2021
# spliceImage.py
# Logic related to export of spliced images.

import wx

LEN_COLUMN = "Curated length (m)"

# Return default pix/m scaling to use for missing images in splice.
# Uses height and curated length of first image encountered.
def getDefaultSpliceScalingAndWidth(imageDict, secsumm):
    scaling = None
    width = None
    for secname, imgpath in imageDict.items():
        section = secsumm._findSectionByFullIdentity(secname)
        if section is not None:
            img = wx.Image(imgpath)
            scaling = img.GetHeight() / section.row[LEN_COLUMN]
            width = img.GetWidth()
            break
    return scaling, width

# Return list of (wx.Image, short section name e.g. A3-5, end of interval bool) tuples in top-to-bottom order
def prepareImagesForSplice(imageDict, secsumm, sitDF):
    images = []
    spliceRows = []
    defaultScaling, defaultWidth = getDefaultSpliceScalingAndWidth(imageDict, secsumm)
    # print("Default scaling = {}".format(defaultScaling))
    for _, row in sitDF.iterrows():
        hole, core = row['Hole'], row['Core']
        top_sec, top_sec_depth = int(row['Top Section']), row['Top Offset']
        bot_sec, bot_sec_depth = int(row['Bottom Section']), row['Bottom Offset']
        secrows = secsumm.getSectionRows(hole, core)
        print("Interval hole {} core {} top_sec {}, bot_sec {}".format(hole, core, top_sec, bot_sec))
        for sr in secrows:
            if int(sr.section) >= top_sec and int(sr.section) <= bot_sec:
                secname = sr.fullIdentity()
                if secname in imageDict:
                    # print("Found matching image file {}".format(imageDict[secname]))
                    img = trimSpliceImage(wx.Image(imageDict[secname]), top_sec, top_sec_depth, bot_sec, bot_sec_depth, int(sr.section), sr.row[LEN_COLUMN])
                else: # create blank image to fill the space
                    print("No image file for section name {}, creating empty image...".format(secname))
                    sec_len_m = sr.row[LEN_COLUMN]
                    if int(sr.section) == top_sec:
                        sec_len_m -= (top_sec_depth/100.0)
                        print("Trimming {}cm from top".format(top_sec_depth))
                    if int(sr.section) == bot_sec:
                        diff = (sr.row[LEN_COLUMN] - (bot_sec_depth/100.0))
                        sec_len_m -= diff
                        print("Trimming {}cm from bottom".format(diff * 100.0))
                    height = round(sec_len_m * defaultScaling)
                    img = wx.EmptyImage(defaultWidth, height)
                    img.SetRGBRect(wx.Rect(0, 0, defaultWidth, height), 0, 0, 255)
                short_secname = "{}{}-{}".format(sr.hole, sr.core, sr.section)
                images.append((img, short_secname, int(sr.section) == bot_sec))
    return images

# Return image trimmed to splice interval.
# img: wx.Image to trim
# top_sec: top section number of splice interval
# top_sec_depth: top section depth in m
# bot_sec: bottom section number of splice interval
# bot_sec_depth: bottom section depth in m
# sec_num: section number of image to be trimmed
# sec_length: length of section in m
def trimSpliceImage(img, top_sec, top_sec_depth, bot_sec, bot_sec_depth, sec_num, sec_length):
    # determine scaling based on height and curated length
    scale = img.GetHeight() / sec_length
    # print("img height {}pix / Curated Length {}m = {} pix/m".format(img.GetHeight(), sec_length, scale))
    top_pix = 0
    bot_pix = img.GetHeight() - 1
    if sec_num not in [top_sec, bot_sec]:
        return img
    else:
        if sec_num == top_sec: # trim top
            top_depth_m = top_sec_depth / 100.0 # cm to m
            top_pix = round(top_depth_m * scale)
            # print("Top depth {}m -> {} top pix".format(top_depth_m, top_pix))
        if sec_num == bot_sec: # trim bottom
            bot_depth_m = bot_sec_depth / 100.0
            bot_pix = round(bot_depth_m * scale)
            # print("Bottom depth {}m -> {} top pix".format(bot_depth_m, bot_pix))
        trim_rect = wx.Rect(0, top_pix, img.GetWidth(), bot_pix - top_pix)
        # print("Getting rect {} for image {} wide, {} high".format(trim_rect, img.GetWidth(), img.GetHeight()))
        trim_img = img.GetSubImage(trim_rect)
        return trim_img

# Return wx.Image comprising images concatenated vertically
# images: list of (wx.Image, short section name str, interval end bool) tuples
# options: draw options
def createSpliceImage(images, options):
    INFO_COL_WIDTH = 200
    spliceHeight = sum([i.GetHeight() for i, _, _ in images])
    spliceWidth = images[0][0].GetWidth()
    if True in options.values(): # add space for info column if any option was selected
        spliceWidth += INFO_COL_WIDTH

    # prepare empty image with black background
    spliceImage = wx.EmptyImage(spliceWidth, spliceHeight)
    r = wx.Rect(0, 0, spliceWidth, spliceHeight)
    spliceImage.SetRGBRect(r, 0, 0, 0)
    y_pos = 0
    for img, secname, interval_end in images:
        if img is not None:
            spliceImage.Paste(img, 0, y_pos)
        y_pos += img.GetHeight()
        if options['sectionLines'] or options['intervalLines']:
            line_height = 2
            x, y, w, h = spliceWidth-INFO_COL_WIDTH, y_pos-line_height, INFO_COL_WIDTH, line_height
            l = wx.Rect(x,y,w,h)
            if not interval_end and options['sectionLines']:
                spliceImage.SetRGBRect(l, 255, 0, 0)
            if interval_end and options['intervalLines']:
                spliceImage.SetRGBRect(l, 0, 255, 0)				
        if options['sectionNames']:
            bmp = spliceImage.ConvertToBitmap() # expensive? could add all text at the end...
            dc = wx.MemoryDC()
            dc.SelectObject(bmp)
            dc.SetPen(wx.Pen(wx.WHITE, 1))
            dc.SetFont(wx.Font(36, wx.SWISS, wx.NORMAL, wx.BOLD))
            dc.SetTextForeground(wx.WHITE)
            w,h = dc.GetTextExtent(secname)
            dc.DrawText(secname, spliceWidth - INFO_COL_WIDTH + 5, y_pos - (h + 5))
            spliceImage = bmp.ConvertToImage()
    return spliceImage