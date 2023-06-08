# SCompoundWidget



这个类是单一子槽类，很多可以挂单个控件的类都会从这个类基础。



它的内部定义了一个槽类，可以挂载一个子SWidget，我们可以看看它的结构。

```c++
struct FCompoundWidgetOneChildSlot : ::TSingleWidgetChildrenWithBasicLayoutSlot<EInvalidateWidgetReason::None>
{
	friend SCompoundWidget;
	using ::TSingleWidgetChildrenWithBasicLayoutSlot<EInvalidateWidgetReason::None>::TSingleWidgetChildrenWithBasicLayoutSlot;//单一widget children和基础布局槽
};
```



它从一个TSingleWidgetChildrenWithBasicLayoutSlot继承，这个类可以挂载一个SWidget以及有一套遍历Children的接口，这里只有一个，不用管，可以看看布局计算这篇文章。



```c++
template<EInvalidateWidgetReason InPaddingInvalidationReason = EInvalidateWidgetReason::Layout>
class TSingleWidgetChildrenWithBasicLayoutSlot : public TSingleWidgetChildrenWithSlot<TSingleWidgetChildrenWithBasicLayoutSlot<InPaddingInvalidationReason>>
	, public TPaddingSingleWidgetSlotMixin<TSingleWidgetChildrenWithBasicLayoutSlot<InPaddingInvalidationReason>, InPaddingInvalidationReason>
	, public TAlignmentSingleWidgetSlotMixin<TSingleWidgetChildrenWithBasicLayoutSlot<InPaddingInvalidationReason>>
{
	//...
}
```

这是一个模板类，从3个模板类继承，模板参数暂时不用管，这个是个枚举值，用来标记一个属性的。

然后这里使用了CRTP，奇异递归模板模式，主要是为了使用链式编程，也就是我们的声明式语法，还有C++编程技巧mixin，

mixin主要用来复用接口用的。



```C++
TSingleWidgetChildrenWithSlot //拥有一个SWidget的智能指针，到时候链式编程的时候赋值上去

TPaddingSingleWidgetSlotMixin //拥有一个FMargin，可以控制一个控件周围的填充

TAlignmentSingleWidgetSlotMixin //存了两个对齐的枚举值，水平对齐和垂直对齐
```



## TSingleWidgetChildrenWithSlot

这个类从FChildren和TSlotBase<SlotType>继承过来，同时拥有遍历和持有子SWidget的功能。

但是这是一个单一子槽节点，只能挂一个子节点。



我们看看FChildren，它只存了一个裸指针，SWidget的裸指针，只读的，不享有所有权，可以访问父级的SWidget。

它有如下的接口：

```c++
virtual int32 Num() const = 0;

virtual TSharedRef<SWidget> GetChildAt(int32 Index) = 0;//反正只有一个，Index只能填0

SWidget& GetOwner() const { return *Owner; }//返回父SWidget的裸指针，只读用的

//还有一些接口，可以自己看
```



```c++
class FSlotBase
{
private:
	TSharedRef<SWidget> Widget;//可以挂一个SWidget，这个最重要
};

template<typename SlotType>
class TSlotBase : public FSlotBase
{
public:
	SlotType& operator[](const TSharedRef<SWidget>& InChildWidget)
	{
		this->AttachWidget(InChildWidget);//这个函数很重要，可以连接SWidget
		return static_cast<SlotType&>(*this);//链式编程
	}
};
```



这里重载了括号运算符，可以挂载一个SWidget，比如：

```c++
SNew(SBorder)
[
	SNew(SButton)//背景板下挂一个SButton
];
```



AttachWidget主要就是起赋值作用，还有把之前挂载的SWidget的给断开。



## TPaddingSingleWidgetSlotMixin

```c++
//存了一个FMargin
SlateAttributePrivate::TSlateMemberAttribute<FMargin>
```



FMargin是一个边距类，存了4个浮点值。

```c++
struct FMargin
{
	float Left;
	float Top;
	float Right;
	float Bottom;
};
```



## TAlignmentSingleWidgetSlotMixin

存了两个枚举值

```c++
EHorizontalAlignment HAlignment;

EVerticalAlignment VAlignment;
```



这些属性都在OnArrange函数里面会用到，会布局好，放入FArrangedChildren里面。



## ComputeDesiredSize

我们看一下，固定大小是怎么计算的：

```c++
FVector2D SCompoundWidget::ComputeDesiredSize( float ) const
{
	EVisibility ChildVisibility = ChildSlot.GetWidget()->GetVisibility();
	if ( ChildVisibility != EVisibility::Collapsed )
	{
        //子槽的固定大小 + 子槽的边距大小
		return ChildSlot.GetWidget()->GetDesiredSize() + ChildSlot.GetPadding().GetDesiredSize();
	}
	
	return FVector2D::ZeroVector;
}
```



## OnPaint

我们看一下OnPaint函数。



```c++
int32 SCompoundWidget::OnPaint( const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect, FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled ) const
{
	//一个CompoundWidget只画它的儿子
	FArrangedChildren ArrangedChildren(EVisibility::Visble);
	{
		this->ArrangeChildren(AllottedGeometry, ArrangedChildren);//分配空间给它的子控件，会转去调用OnArrange函数
	}
	
    //是否开启，如果父亲这个属性标记为未开启，这个也会未开启，就不会绘制
	const bool bShouldBeEnabled = ShoulBeEnabled(bParentEnabled);
    
    //获取排列好的子widget
    FArrangedWidget& TheChild = ArrangedChildren[0];
    
    //FWidgetStyle和之前篇章描述的style不一样，就是3个FLinearColor，会一直递归传递下去，一直混合
    FWidgetStyle CompoundedWidgetStyle = FWidgetStyle(InWidgetStyle)
        .BlendColorAndOpacityTint(GetColorAndOpacity())
        .SetForegroundColor(bShouldBeEnabled ? GetForegroundColor() : GetDisabledForegroundColor() );
    
    int32 Layer = 0;
    
    //递归画儿子
    Layer = TheChild.Widget->Paint( Args.WithNewParent(this), TheChild.Geometry, MyCullingRect, OutDrawElements, LayerId + 1, CompoundedWidgetStyle, bShouldBeEnabled);
    
    return Layer;
}
```



## OnArrangeChildren

这个会调用ArrangeSingleChild。



```c++
void SCompoundWidget::OnArrangeChildren( const FGeometry& AllottedGeometry, FArrangedChildren& ArrangedChildren ) const
{
	ArrangeSingleChild(GSlateFlowDirection, AllottedGeometry, ArrangedChildren, ChildSlot, GetContentScale());
}
```



ArrangeSingleChildren分配布局给子控件，我们看看怎么分配的：

```c++
template<typename SlotType>
static void ArrangeSingleChild(EFlowDirection InFlowDirection, const FGeometry& AllottedGeometry, FArrangedChildren& ArrangedChildren, const SlotType& ChildSlot, const FVector2D& ContentScale)
{
    //获取可见性
    const EVisibility ChildVisibility = ChildSlot.GetWidget()->GetVisibility();
    
    //这个可见性是满足的，一般都是EVisibility::Visible
    if (ArrangedChildren.Accepts(ChildVisibility))
	{
		const FVector2D ThisContentScale = ContentScale;
        //计算填充，这个InFlowDirection一般都是从左往右，是个全局变量
        //如果是从右往左，就交换左右边距
		const FMargin SlotPadding(LayoutPaddingWithFlow(InFlowDirection, ChildSlot.GetPadding()));
		const AlignmentArrangeResult XResult = AlignChild<Orient_Horizontal>(InFlowDirection, AllottedGeometry.GetLocalSize().X, ChildSlot, SlotPadding, ThisContentScale.X);
		const AlignmentArrangeResult YResult = AlignChild<Orient_Vertical>(AllottedGeometry.GetLocalSize().Y, ChildSlot, SlotPadding, ThisContentScale.Y);

        //放入安排好的儿子到ArrangedChildren数组
		ArrangedChildren.AddWidget(ChildVisibility, AllottedGeometry.MakeChild(
			ChildSlot.GetWidget(),
			FVector2D(XResult.Offset, YResult.Offset),
			FVector2D(XResult.Size, YResult.Size)
		));
	}
}
```



我们看一下AlignChild这个函数，是怎么控制单个儿子控件的布局的：

### AlignChild

这个AlignmentArrangeResult就存了两个浮点值，一个偏移，一个大小。

```c++
template<EOrientation Orientation, typename SlotType>
static AlignmentArrangeResult AlignChild(EFlowDirection InLayoutFlow, float AllottedSize, float ChildDesiredSize, const SlotType& ChildToArrange, const FMargin& SlotPadding, const float& ContentScale = 1.0f, bool bClampToParent = true)
{
	const FMargin& Margin = SlotPadding;
	const float TotalMargin = Margin.GetTotalSpaceAlong<Orientation>();
	const float MarginPre = ( Orientation == Orient_Horizontal ) ? Margin.Left : Margin.Top;
	const float MarginPost = ( Orientation == Orient_Horizontal ) ? Margin.Right : Margin.Bottom;

	const int32 Alignment = ArrangeUtils::GetChildAlignment<Orientation>::AsInt(InLayoutFlow, ChildToArrange);

    //如果指定为水平填充，则会减去边距后，剩余的所有空间都留给子控件
	switch (Alignment)
	{
	case HAlign_Fill:
		return AlignmentArrangeResult(MarginPre, FMath::Max((AllottedSize - TotalMargin) * ContentScale, 0.f));
	}
	
	const float ChildSize = FMath::Max((bClampToParent ? FMath::Min(ChildDesiredSize, AllottedSize - TotalMargin) : ChildDesiredSize), 0.f);

    //其余情况全部使用固定大小
	switch( Alignment )
	{
	case HAlign_Left: // same as Align_Top
		return AlignmentArrangeResult(MarginPre, ChildSize);
	case HAlign_Center:
		return AlignmentArrangeResult(( AllottedSize - ChildSize ) / 2.0f + MarginPre - MarginPost, ChildSize);
	case HAlign_Right: // same as Align_Bottom		
		return AlignmentArrangeResult(AllottedSize - ChildSize - MarginPost, ChildSize);
	}

	// Same as Fill
	return AlignmentArrangeResult(MarginPre, FMath::Max(( AllottedSize - TotalMargin ) * ContentScale, 0.f));
}
```



ComputeDesiredSize的作用就体现在这里，第一次递归计算固定大小，然后如果这个控件指定了填充，那么就不考虑这个固定大小，否则则考虑固定大小。



































