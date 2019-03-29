# NeteaseMusic
网易云音乐。抓取听歌排行、精彩评论、所有评论接口访问封装。

## 使用
```
from NeteaseMusic import NeteaseMusic

necc = NeteaseMusic()

# 获取所有评论
necc.get_all_comment(song_id) #dict
# 获取热门评论
necc.get_hot_comment(song_id) #dict
# 获取听歌排行
necc.get_listening_list(user_id) #list
```
