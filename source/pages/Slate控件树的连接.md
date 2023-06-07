# Slate控件树的连接

父子控件的连接是通过槽实现的，正常的UI实现的话，通过如下的方式：

```c++
class Widget
{
public:
	std::vector<std::shared_ptr<Widget>> m_widgets;//一堆儿子，然后递归遍历控件
};
```



但是Slate通过这种方式：

```c++
class SCompoundWidget
{
    //子槽
	FCompoundWidgetOneChildSlot ChildSlot;
};

//由槽来持有儿子控件

```

至于为什么要这样做？因为Slate对槽赋予了布局的概念，槽还携带对齐、填充(padding)等属性。

然后槽类有很多，单独定义在每个控件类里面，有画板槽类，单一子槽等。



每个带有连接特质的控件都会在类里面定义一个槽类，比如SCompoundWidget可以挂一个儿子控件，SOverlay可以挂一堆儿子。



我们看看SOverlay的槽类：

```c++
class SOverlay : public SPanel
{
	/*一个槽支持内容的对齐还有填充，还有z-order*/
	class FOverlaySlot : public TBasicLayoutWidgetSlot<FOverlaySlot>
	{
	public:
		FOverlaySlot(int32 InZOrder)
			: TBasicLayoutWidgetSlot<FOverlaySlot>(HAlign_Fill, VAlign_Fill)
			, ZOrder(InZOrder)
		{}
	public:
		int32 ZOrder;
	};
    
    TPanelChildren<FOverlaySlot> Children;//SOverlay持有一个槽数组
}
```



TBasicLayoutWidgetSlot这个模板类，持有一个SWidget的智能指针，可以挂一个SWidget。类图可以在布局计算中查看。



TPanelChildren是一个类似数组的模板类，针对槽增加了一些比较好用的接口。



让我们看看UMG里面用的最多的控件SConstraintCanvas：

```c++
class SConstraintCanvas : public SPanel
{
	class FSlot : public TSlotBase<FSlot>
	{
	public:
		TAttribute<FMargin> OffsetAttr;
		
		TAttribute<FAnchors> AnchorsAttr;
		
		TAttribute<FVector2D> AlignmentAttr;
		
		TAttribute<bool> AutoSizeAttr;
		
		//TAttribute<float> ZOrderAttr;
		
		float ZOrder;
	};
	
	TPanelChildren<FSlot> Children;
};
```



在布局计算这篇文章里面，布局的具体计算是在OnArrange这个虚函数里面，会在这个OnArrange里面根据槽的属性，计算布局，比如根据ZOrder计算出Layer，然后排列好，存放到FArrangedChildren(已经安排好的孩子)里面，FArrangedChildren类可以看看布局计算这篇文章，是个FArrangedWidget的数组，FArrangedWidget由SWidget和FGeometry组成。

















