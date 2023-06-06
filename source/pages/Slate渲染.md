# Slate的渲染

Slate是逐窗口渲染，如果是手机的话，就只要画一个就行了。



窗口的创建，依赖于平台，在Windows和Mac上要根据操作系统的API创建，为了屏蔽这个差异性，Unreal使用FGenericWindow作为基类，然后从这个FGenericWindow派生不同平台的窗口子类，比如FWindowsWindow这个类，然后在其内部持有HWND，windows窗口系统的窗口句柄，我们在虚函数里面调用Win32的函数对这个窗口进行操作。



Slate有一个逻辑窗口类，以及相应的平台窗口类，逻辑窗口类是SWindow，也就是正常的控件，它持有一个

```c++
TSharedPtr<FGenericWindow> NativeWindow;//native window handle
```

这样做的目的是，为了让窗口这种依赖于平台的也和其它控件的创建和操作保持一致。

![](_static/Image/Slate/SWindow.png)

这是SWindow的参数类，里面有很多，比如窗口类型(普通的，弹出窗口，模态的)，还有风格(FWindowStyle)，标题，创建的时候是否居中，左上角位置，是否支持透明，初始的透明度，有很多很多属性。在Construct里面进行一些额外的处理，并且赋值完毕后。

之后，可以通过FSlateApplication的AddWindow函数来创建平台窗口。

```C++
virtual TSharedRef<SWindow> AddWindow( TSharedRef<SWindow> InSlateWindow, const bool bShowImmediately = true ) override;//这个bShowImmediately控制这个窗口是否立即创建RenderTarget，用于窗口的绘制
```



```c++
TSharedRef<SWindow> FSlateApplication::AddWindow(TSharedRef<SWindow> InSlateWindow, const bool bShowImmediately = true)
{
    //这个函数会排序，把这个窗口和之前打开过的窗口排个序，保持ZOrder，主要用于鼠标事件的穿透路由，从顶层窗口散播下去
	FSlateWindowHelper::ArrangeWindowToFront(SlateWindows, InSlateWindow);
    //创建平台窗口，为这个SWindow逻辑窗口创建相应的native window handle
	TSharedRef<FGenericWindow> NewWindow = MakeWindow( InSlateWindow, bShowImmediately );
    
    //立即创建back buffer，图形API需要传入native window的句柄，创建back buffer
    if(bShowImmediately)
    {
        InSlateWindow->ShowWindow();//这个函数会创建back buffer
        
        //设置焦点...
    }
    
    return InSlateWindow;
}
```



ShowWindow这个函数比较重要，里面为会这个窗口创建相应的backbuffer以及相应的正交透视矩阵：

```c++
void SWindow::ShowWindow()
{
	if(NativeWindow) //判断关联的native window是否已经创建
	{
		//这个函数，获取application的渲染器，然后创建视口，创建backbuffer
		FSlateApplicationBase::Get().GetRenderer()->CreateViewport(SharedThis(this));
	}
	
	//...
}
```



Application也和SWindow差不多，也有逻辑Application和平台Application，平台Application主要是针对不同平台子类的Application进行派生，比如FWindowsApplication，它从GenericApplication派生，然后FSlateApplicationBase持有GenericApplication的单例。这样做的目的是处理不同平台的消息派发。



Windows[的消息循环在这里](https://learn.microsoft.com/en-us/windows/win32/winmsg/using-messages-and-message-queues)，这些在FWindowsApplication里面。



可惜的是，操作系统的鼠标、键盘消息、窗口、图形渲染全是native的，这些都需要进一步封装。



FSlateApplicationBase类持有FSlateRenderer，Slate的渲染器，它同样也有相应的子类，总共3个，FSlateD3DRenderer，FSlateOpenGLRenderer，FSlateRHIRenderer，第一个和第二个是裸着调用图形API的，第三个是封装了图形模块的RHI，这个RHI封装了OpenGL和DirectX和Vulkan等图形API，在不同平台进行切换。Slate可以编写单独的应用，会使用第一个和第二个，如果是正常的流程，则是第三个。

```c++
void FSlateRHIRenderer::CreateViewport(const TSharedRef<SWindow> Window)
{
	FViewportInfo* NewInfo = new FViewportInfo();//创建一个FViewportInfo类
    
    //拿到native window handle
    TSharedRef<FGenericWindow> NativeWindow = Window->GetNativeWindow().ToSharedRef();
    NewInfo->OSWindow = NativeWindow->GetOSWindowHandle();//获取native window hand
    NewInfo->Width = Width;
    NewInfo->Height = Height;
    NewInfo->DesiredWidth = Width;
    NewInfo->DesiredHeight = Height;
    //创建正交投影矩阵，画UI用的
    NewInfo->ProjectionMatrix = CreateProjectionMatrix(Width, Height);
    
    //这个viewport存储了backbuffer，像素格式，交换链
    NewInfo->ViewportRHI = RHICreateViewport(NewInfo->OSWindow, Width, Height, bFullscreen, NewInfo->PixelFormat);
    
    WindowToViewportInfo.Add(&Window.Get(), NewInfo);//加入到渲染器的map里面，SWindow做Key，FViewportInfo做值
    //后续逐窗口渲染的时候，通过SWindow查找FViewportInfo，然后画到窗口的back buffer上面
}
```



这里FSlateRHIRenderer把backbuffer抽象成了FViewportRHI，但是另外两个裸着调用图形API的渲染器是直接存了backbuffer的，如果想学RHI，可以对照着这3个类看看。



FSlateApplication的初始化和渲染器的初始化在FEngineLoop::PreInitPreStartupScreen里面，还有一些基础风格的初始化也在里面。



```c++
FSlateApplication::InitHighDPI(bForceEnableHighDPI);//这个dpi会根据操作系统的设置动态改变

FSlateApplication::Create();//初始化平台Application，如果是Windows，则会注册操作系统的消息回调

FSlateApplication::InitializeCoreStyle();

TSharedPtr<FSlateRenderer> SlateRenderer = GUsingNullRHI ?
FModuleManager::Get().LoadModuleChecked<ISlateNullRendererModule>("SlateNullRenderer").CreateSlateNullRenderer() :
FModuleManager::Get().GetModuleChecked<ISlateRHIRendererModule>("SlateRHIRenderer").CreateSlateRHIRenderer();
TSharedRef<FSlateRenderer> SlateRendererSharedRef = SlateRenderer.ToSharedRef();//创建slate渲染器

FSlateApplication& CurrentSlateApp = FSlateApplication::Get();
CurrentSlateApp.InitializeRenderer(SlateRendererSharedRef);//初始化渲染器
```

![](_static/Image/Slate/dpi.png)

dpi是这个，主要是如果这个改动了，程序也要通过WIN32的API获取dpi值，然后把所有控件跟着一起缩放。



FSlateRHIRenderer的Initialize函数会初始化一些成员变量：

```c++
bool FSlateRHIRenderer::Initialize()
{
	LoadUsedTextures();//加载控件用到的画刷，也就是贴图，没用到的，不加载，会创建显存buffer

	RenderingPolicy = MakeShareable(new FSlateRHIRenderingPolicy(SlateFontServices.ToSharedRef(), ResourceManager.ToSharedRef()));//创建渲染策略，这个在FSlateRHIRenderer的DrawWindow函数里面会使用

	ElementBatcher = MakeUnique<FSlateElementBatcher>(RenderingPolicy.ToSharedRef());//合批器，把一些相同图集的控件给合批了的类
    
	return true;
}
```



FSlateRHIRenderer持有一个FSlateDrawBuffer，这个是FSlateWindowElementList的数组，每个窗口一个FSlateWindowElementList，每一帧都会生成控件的顶点数据、索引数据，还有其它数据放置在这个FSlateWindowElementList里面，FSlateWindowElementList存了一个FSlateBatchData，FSlateBatchData则是FSlateRenderBatch的数组，每个控件一个FSlateRenderBatch，如果合批器合批了，则可能多个控件合并到一个FSlateRenderBatch。

```c++
FSlateRnederBatch的成员变量
    
FShaderParams ShaderParams;//着色器参数

FSlateVertexArray* SourceVertices;//顶点数组

FSlateIndexArray* SourceIndices;//索引数组

int32_t LayerId;//当前这个控件的层，合批器合批的时候，会判断两个控件的Layer是否一样，一样的话，就合并顶点、索引

ESlateBatchDrawFlag DrawFlags;

ESlateShader ShaderType;

ESlateDrawPrimitive DrawPrimitiveType;

ESlateDrawEffect DrawEffects;
```



合批控件的条件非常苛刻，在绘制每一帧前，会合批一下：



在ElementBatch.cpp的MergeRenderBatches函数里面，会合批控件：

```c++
//首先根据层从小到大稳定排序
TArray<TPair<int32, int32>, TInlineAllocator<100, TMemStackAllocator<>>> BatchIndices;

{
	BatchIndices.AddUninitialized(RenderBatches.Num());
	
	for(int32 Index = 0; Index < RenderBatches.Num(); ++Index)
	{
		BatchIndices[Index].Key = Index;
		BatchIndices[Index].Value = RenderBatches[Index].GetLayer();//获取一个FSlateRenderBatch的layer
	}
	
	//稳定排序，根据layer进行排序
	BatchIndices.StableSort
	{
		[](const TPair<int32, int32>& A, const TPair<int32, int32>& B)
		{
			return A.Value < B.Value;
		}
	}
}

//从前往后开始合并
NumBatches = 0;
NumLayers = 0;

int32 CurLayerId = INDEX_NONE;//当前render batch的layer id
int32 PrevLayerId = INDEX_NONE;//前面render batch的layer id

FirstRenderBatchIndex = BatchIndices[0].Key;

FSlateRenderBatch* PrevBatch = nullptr;
//从前往后开始合并
for(int32 BatchIndex = 0; BatchIndex < BatchIndices.Num(); ++BatchIndex)
{
    const TPair<in32, int32>& BatchIndexPair = BatchIndices[BatchIndex];
    
    CurLayerId = CurBatch.GetLayer();//获取当前batch的layer
    
    if(PrevLayerId != CurLayerId)
    {
        ++NumLayers;//当前render batch和前面的不一样，增加NumLayers
    }
    
    if(PrevBatch != nullptr)
    {
        PrevBatch->NextBatchIndex = BatchIndexPair.Key;//用链表串起来
    }
    
    ++NumBatches;
    
    FillBuffersFromNewBatch(CurBatch, FinalVertexData, FinalIndexData);
    
    //开始合并
    if(CurBatch.bIsMergable)
    {
        for(int32 TestIndex = BatchIndex + 1; TestIndex < BatchIndices.Num(); ++TestIndex)
        {
            const TPair<int32, int32>& NextBatchIndexPair = BatchIndices[TestIndex];
            FSlateRenderBatch& TestBatch = RenderBatches[NextBatchIndexPair.Key];
            if(TestBatch.GetLayer() != CurBatch.GetLayer())
            {
                break;
            }
            else if(!TestBatch.bIsMerged && CurBatch.IsBatchableWith(TestBatch))
            {
                CombineBatches(CurBatch, TestBatch, FinalVertexData, FinalIndexData);//合并batch
            }
        }
    }
    PrevBatch = &CurBatch;
}
```



```c++
//class FSlateRenderBatch
bool IsBatchableWith(const FSlateRenderBatch& Other) const
{
	return
		ShaderResource == Other.ShaderResource
		&& DrawFlags == Other.DrawFlags
		&& ShaderType == Other.ShaderType
		&& DrawPrimitiveType == Other.DrawPrimitiveType
		&& DrawEffects == Other.DrawEffects
		&& ShaderParams == Other.ShaderParams
		&& InstanceData == Other.InstanceData
		&& InstanceCount == Other.InstanceCount
		&& InstanceOffset == Other.InstanceOffset
		&& DynamicOffset == Other.DynamicOffset
		&& CustomDrawer == Other.CustomDrawer
		&& SceneIndex == Other.SceneIndex
		&& ClippingState == Other.ClippingState;
}
```

需要满足很多条件，才可以合批，着色器资源也要一样(这个是DirectX的描述符，或者是OpenGL的纹理ID)，层要一样，图元拓扑也要一样。



## 控件的渲染

控件首先需要自下而上递归，计算一次固定大小(desired size)，然后自上而下递归，计算布局，把整个窗口的几何大小分配给每个控件，为啥要两次递归？因为控件有些指定自动大小的，会进行布局的计算，而不会使用图片的固定大小。



然后绘制是第三次递归，总共遍历3次控件树，还有一次是消息事件的路由，总共4次递归，有3次可以合并，绘制，分配几何大小，2D碰撞网格的构建可以合并，这些都在OnPaint里面处理。



布局的计算是在OnPaint一开头，可以查看布局计算这篇文章。



持续更新。































