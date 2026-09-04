# 数据来源

`pingshui.json`（平水韵，含入声）与 `xinyun.json`（中华新韵·十四韵）转自
开源仓库 **charlesix59/chinese_word_rhyme**（data/Pingshui_Rhyme.json、data/Xinyun_Rhyme.json），
已按「字 → [[韵部, 声调]]」反向索引、收集多音字全部读音。

- 上游: https://github.com/charlesix59/chinese_word_rhyme
- 许可: MIT License
- 平水韵声调标签: 上平/下平=平；上/去/入=仄（入声即普通话易误判处）。
- 新韵声调标签: 平/仄（无入声，按普通话）。

`charfreq.txt`：6763 个常用汉字按使用频率从高到低排列，供 `yun` 子命令把常用韵脚排前、生僻字沉底。
- 上游: https://github.com/sxei/pinyinjs （other/常用6763个汉字使用频率表.txt）
- 用法: 索引即排名（越小越常用）；不在表中的字视为生僻，排末。
