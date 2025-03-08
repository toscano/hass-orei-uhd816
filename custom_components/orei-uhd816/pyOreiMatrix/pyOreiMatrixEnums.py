from enum import IntEnum

class DescriptiveIntEnum(IntEnum):
    def __new__(cls, value, description=None):
        member = int.__new__(cls, value)
        member._value_ = value
        member.description = description
        return member

    @property
    def describe(self):
      return self.description


class EDID(DescriptiveIntEnum):
    """Enum for setting the EDID."""
    EDID_1080P_STEREO_AUDIO_2_0         =  0, "1080p,Stereo Audio 2.0"
    EDID_1080P_DOLBY_DTS_5_1            =  1, "1080p,Dolby/DTS 5.1"
    EDID_1080P_HD_AUDIO_7_1             =  2, "1080p,HD Audio 7.1"
    EDID_1080I_STEREO_AUDIO_2_0         =  3, "1080i,Stereo Audio 2.0"
    DID_1080I_DOLBY_DTS_5_1             =  4, "1080i,Dolby/DTS 5.1"
    EDID_1080I_HD_AUDIO_7_1             =  5, "1080i,HD Audio 7.1"
    EDID_3D_STEREO_AUDIO_2_0            =  6, "3D,Stereo Audio 2.0"
    EDID_3D_DOLBY_DTS_5_1               =  7, "3D,Dolby/DTS 5.1"
    EDID_3D_HD_AUDIO_7_1                =  8, "3D,HD Audio 7.1"
    EDID_4K2K30_444_STEREO_AUDIO_2_0    =  9, "4K2K30_444,Stereo Audio 2.0"
    EDID_4K2K30_444_DOLBY_DTS_5_1       = 10, "4K2K30_444,Dolby/DTS 5.1"
    EDID_4K2K30_444_HD_AUDIO_7_1        = 11, "4K2K30_444,HD Audio 7.1"
    EDID_4K2K60_420_STEREO_AUDIO_2_0    = 12, "4K2K60_420,Stereo Audio 2.0"
    EDID_4K2K60_420_DOLBY_DTS_5_1       = 13, "4K2K60_420,Dolby/DTS 5.1"
    EDID_4K2K60_420_HD_AUDIO_7_1        = 14, "4K2K60_420,HD Audio 7.1"
    EDID_4K2K60_444_STEREO_AUDIO_2_0    = 15, "4K2K60_444,Stereo Audio 2.0"
    EDID_4K2K60_444_DOLBY_DTS_5_1       = 16, "4K2K60_444,Dolby/DTS 5.1"
    EDID_4K2K60_444_HD_AUDIO_7_1        = 17, "4K2K60_444,HD Audio 7.1"
    EDID_4K2K60_444_STEREO_AUDIO_2_0_HDR= 18, "4K2K60_444,Stereo Audio 2.0 HDR"
    EDID_4K2K60_444_DOLBY_DTS_5_1_HDR   = 19, "4K2K60_444,Dolby/DTS 5.1 HDR"
    EDID_4K2K60_444_HD_AUDIO_7_1_HDR    = 20, "4K2K60_444,HD Audio 7.1 HDR"
    EDID_USER_DEFINE_1                  = 21, "User Define1"
    EDID_USER_DEFINE_2                  = 22, "User Define2"
    EDID_COPY_FROM_HDMI_OUT_1           = 23, "copy from hdmi output 1"
    EDID_COPY_FROM_HDMI_OUT_2           = 24, "copy from hdmi output 2"
    EDID_COPY_FROM_HDMI_OUT_3           = 25, "copy from hdmi output 3"
    EDID_COPY_FROM_HDMI_OUT_4           = 26, "copy from hdmi output 4"
    EDID_COPY_FROM_HDMI_OUT_5           = 27, "copy from hdmi output 5"
    EDID_COPY_FROM_HDMI_OUT_6           = 28, "copy from hdmi output 6"
    EDID_COPY_FROM_HDMI_OUT_7           = 29, "copy from hdmi output 7"
    EDID_COPY_FROM_HDMI_OUT_8           = 30, "copy from hdmi output 8"
    EDID_COPY_FROM_CAT_OUT_1            = 31, "copy from cat output 1"
    EDID_COPY_FROM_CAT_OUT_2            = 32, "copy from cat output 2"
    EDID_COPY_FROM_CAT_OUT_3            = 33, "copy from cat output 3"
    EDID_COPY_FROM_CAT_OUT_4            = 34, "copy from cat output 4"
    EDID_COPY_FROM_CAT_OUT_5            = 35, "copy from cat output 5"
    EDID_COPY_FROM_CAT_OUT_6            = 36, "copy from cat output 6"
    EDID_COPY_FROM_CAT_OUT_7            = 37, "copy from cat output 7"
    EDID_COPY_FROM_CAT_OUT_8            = 38, "copy from cat output 8"











































































