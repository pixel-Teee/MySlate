# SWindow以及窗口的创建

Slate的窗口

Slate的窗口控件是SWindow这个类，这个类创建的时候，书写方式如下：

```c++
SAssignNew(root_window, SWindow)
	.Title("hello") //标题
	.ClientSize(...) //窗口大小
	.ScreenPosition(...) //初始化的时候所在的屏幕位置
```

