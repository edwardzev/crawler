"use client";

import React, { useEffect, useRef, useState } from "react";
// Dynamic import for fabric usually needed in Next.js, but "use client" helps.
// We'll import fabric inside useEffect or use a dynamic component wrapper if needed.
// Fabric 5 import:
import { fabric } from "fabric";
import { Upload, RefreshCcw, Share2, Save, Download, Sparkles, X, Image as ImageIcon, Check } from "lucide-react";
import { Product } from "@/lib/types";
import { removeBackground, preload } from "@imgly/background-removal";
import { useOrder } from "@/lib/hooks/useOrder";
import { useToast } from "@/lib/contexts/ToastContext";

interface MockupEditorProps {
    product: Product;
    initialState?: any; // For loading shared mockups
    readOnly?: boolean;
    onClose?: () => void;
}

export default function MockupEditor({ product, initialState, readOnly = false, onClose }: MockupEditorProps) {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const containerRef = useRef<HTMLDivElement>(null);
    const [fabricCanvas, setFabricCanvas] = useState<fabric.Canvas | null>(null);
    const [logoObject, setLogoObject] = useState<fabric.Image | null>(null);
    const [opacity, setOpacity] = useState(1);
    const [blendMode, setBlendMode] = useState<"normal" | "multiply">("normal");
    const [isSharing, setIsSharing] = useState(false);
    const [isProcessingBg, setIsProcessingBg] = useState(false);
    const { orderState, addItem } = useOrder();
    const { showToast } = useToast();

    // AI Model State
    const [isModelReady, setIsModelReady] = useState(false);
    const [isModelDownloading, setIsModelDownloading] = useState(false);
    const [progressText, setProgressText] = useState<string>("");
    const [progressPercent, setProgressPercent] = useState(0);
    const [quantity, setQuantity] = useState<number>(100);
    const [widthCm, setWidthCm] = useState<number>(5);
    const [isSubmitting, setIsSubmitting] = useState(false);

    // Image Selection
    const [selectedImageIndex, setSelectedImageIndex] = useState(0);
    const availableImages = product.images || (product.image_main ? [product.image_main] : []);

    // Preload AI Model on mount
    useEffect(() => {
        if (!readOnly && !isModelReady) {
            setIsModelDownloading(true);
            preload().then(() => {
                console.log("AI Model Preloaded");
                setIsModelReady(true);
                setIsModelDownloading(false);
            }).catch((err) => {
                console.error("Failed to preload AI model", err);
                setIsModelDownloading(false);
            });
        }
    }, [readOnly, isModelReady]);

    // Initial Setup
    useEffect(() => {
        if (!canvasRef.current || !containerRef.current) return;

        const width = containerRef.current.clientWidth || 800;
        const height = containerRef.current.clientHeight || 600;

        const canvas = new fabric.Canvas(canvasRef.current, {
            width: width,
            height: height,
            selection: !readOnly,
            backgroundColor: '#f8f8f8',
            imageSmoothingEnabled: true
        });

        const handleResize = () => {
            if (!containerRef.current) return;
            const w = containerRef.current.clientWidth;
            const h = containerRef.current.clientHeight;

            canvas.setWidth(w);
            canvas.setHeight(h);
            canvas.renderAll();
        };

        setFabricCanvas(canvas);
        console.log("Canvas Initialized", { width, height });

        window.addEventListener('resize', handleResize);

        return () => {
            canvas.dispose();
            window.removeEventListener('resize', handleResize);
        };
    }, [readOnly]);

    // Update Background Image when selection changes
    useEffect(() => {
        if (!fabricCanvas || availableImages.length === 0) return;

        const bgUrl = availableImages[selectedImageIndex] || "/placeholder.png";
        const width = fabricCanvas.getWidth();
        const height = fabricCanvas.getHeight();

        fabric.Image.fromURL(bgUrl, (img) => {
            if (!img || !fabricCanvas) return;

            const cw = fabricCanvas.getWidth();
            const ch = fabricCanvas.getHeight();
            if (cw === 0 || ch === 0) return; // Not ready yet

            const iw = img.width || 1;
            const ih = img.height || 1;

            // Contain Logic: fit everything, keep aspect ratio
            const scale = Math.min(cw / iw, ch / ih);

            // Calculate offsets to center
            const left = (cw - iw * scale) / 2;
            const top = (ch - ih * scale) / 2;

            console.log(`Setting Background: ${bgUrl}`, {
                canvas: { cw, ch },
                img: { iw, ih },
                scale,
                pos: { left, top }
            });

            // Set properties on img FIRST to be safe
            img.set({
                originX: 'left',
                originY: 'top',
                scaleX: scale,
                scaleY: scale,
                left: left,
                top: top,
                selectable: false,
                evented: false,
            });

            // Then set as background
            fabricCanvas.setBackgroundImage(img, () => {
                fabricCanvas.renderAll();
            });
        }, { crossOrigin: 'anonymous' });

    }, [fabricCanvas, selectedImageIndex, availableImages]);


    // Load Initial State if Shared
    useEffect(() => {
        if (fabricCanvas && initialState) {
            // Restore logo
            const { transform, logoSource, selectedImageIndex: savedIndex } = initialState;

            if (savedIndex !== undefined && savedIndex < availableImages.length) {
                setSelectedImageIndex(savedIndex);
            }

            fabric.Image.fromURL(logoSource.src, (img) => {
                if (!img) return;

                const width = fabricCanvas.getWidth();
                const left = transform.x * width;
                const top = transform.y * width;
                const scale = (transform.scaleX * width) / (img.width || 1);

                img.set({
                    left: left,
                    top: top,
                    scaleX: scale,
                    scaleY: scale,
                    angle: transform.rotation,
                    opacity: transform.opacity,
                    originX: 'center',
                    originY: 'center',
                    selectable: !readOnly,
                    evented: !readOnly,
                    globalCompositeOperation: transform.blendMode || "source-over"
                });

                if (transform.blendMode === "multiply") {
                    setBlendMode("multiply");
                }

                fabricCanvas.add(img);
                if (!readOnly) fabricCanvas.setActiveObject(img);
                setLogoObject(img);
                setOpacity(transform.opacity);

            }, { crossOrigin: 'anonymous' });
        }
    }, [fabricCanvas, initialState, readOnly, availableImages]);

    const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file || !fabricCanvas) return;

        const reader = new FileReader();
        reader.onload = (f) => {
            const data = f.target?.result as string;
            loadLogoToCanvas(data);
        };
        reader.readAsDataURL(file);
    };

    const loadLogoToCanvas = (dataUrl: string) => {
        if (!fabricCanvas) return;

        fabric.Image.fromURL(dataUrl, (img) => {
            if (!img) return;

            // Remove existing
            if (logoObject) {
                fabricCanvas.remove(logoObject);
            }

            const canvasWidth = fabricCanvas.getWidth();
            const targetWidth = canvasWidth * 0.4; // Slightly larger default
            const scale = targetWidth / (img.width || 1);

            img.set({
                left: canvasWidth / 2,
                top: canvasWidth / 2,
                originX: 'center',
                originY: 'center',
                scaleX: scale,
                scaleY: scale,
                cornerSize: 12,
                transparentCorners: false,
                cornerColor: '#3B82F6',
                borderColor: '#3B82F6',
                borderDashArray: [4, 4],
            });

            fabricCanvas.add(img);
            fabricCanvas.setActiveObject(img);
            setLogoObject(img);
            setOpacity(1);
            setBlendMode("normal"); // Reset blend mode on new upload
        });
    };

    const [selectedObjectPos, setSelectedObjectPos] = useState<{ x: number, y: number } | null>(null);

    useEffect(() => {
        if (!fabricCanvas) return;

        const updatePos = () => {
            const active = fabricCanvas.getActiveObject();
            if (active && active === logoObject) {
                const boundingRect = active.getBoundingRect();
                setSelectedObjectPos({
                    x: boundingRect.left + boundingRect.width,
                    y: boundingRect.top
                });
            } else {
                setSelectedObjectPos(null);
            }
        };

        fabricCanvas.on('selection:created', updatePos);
        fabricCanvas.on('selection:updated', updatePos);
        fabricCanvas.on('object:moving', updatePos);
        fabricCanvas.on('object:scaling', updatePos);
        fabricCanvas.on('object:rotating', updatePos);
        fabricCanvas.on('selection:cleared', () => setSelectedObjectPos(null));

        return () => {
            fabricCanvas.off('selection:created', updatePos);
            fabricCanvas.off('selection:updated', updatePos);
            fabricCanvas.off('object:moving', updatePos);
            fabricCanvas.off('object:scaling', updatePos);
            fabricCanvas.off('object:rotating', updatePos);
            fabricCanvas.off('selection:cleared');
        };
    }, [fabricCanvas, logoObject]);

    const handleRemoveBackground = async () => {
        if (!logoObject) return;

        setIsProcessingBg(true);
        try {
            // Get original src as Blob/URL
            const src = logoObject.getSrc();

            // Note: Cloudinary URLs might have CORS issues if not configured.
            // But usually logos are uploaded via blob: or base64 data url from file input here.

            // Convert to blob
            const response = await fetch(src);
            const blob = await response.blob();

            // Process
            const removedBgBlob = await removeBackground(blob, {
                progress: (key, current, total) => {
                    if (key.startsWith("fetch")) {
                        const percent = Math.round((current / total) * 100);
                        setProgressText(`מוריד מודל: ${percent}%`);
                        setProgressPercent(percent);
                    } else if (key.startsWith("compute")) {
                        // Some models don't send total, assume 100 or fake it
                        const percent = total > 0 ? Math.round((current / total) * 100) : 0;
                        setProgressText(`מעבד: ${percent}%`);
                        setProgressPercent(percent);
                    }
                }
            });
            const url = URL.createObjectURL(removedBgBlob);

            // Replace image on canvas keeping props
            const props = {
                left: logoObject.left,
                top: logoObject.top,
                scaleX: logoObject.scaleX,
                scaleY: logoObject.scaleY,
                angle: logoObject.angle,
                opacity: logoObject.opacity,
                originX: logoObject.originX,
                originY: logoObject.originY,
                selectable: !readOnly,
                evented: !readOnly,
                globalCompositeOperation: logoObject.globalCompositeOperation
            };

            fabric.Image.fromURL(url, (newImg) => {
                fabricCanvas?.remove(logoObject);
                newImg.set(props);
                fabricCanvas?.add(newImg);
                fabricCanvas?.setActiveObject(newImg);
                setLogoObject(newImg);
                fabricCanvas?.requestRenderAll();
            });

        } catch (e) {
            console.error(e);
            showToast("הסרת רקע נכשלה. נסה תמונה אחרת.", "error");
        } finally {
            setIsProcessingBg(false);
            setProgressText("");
            setProgressPercent(0);
        }
    };

    const removeLogo = () => {
        if (!logoObject || !fabricCanvas) return;
        fabricCanvas.remove(logoObject);
        setLogoObject(null);
        setSelectedObjectPos(null);
        fabricCanvas.requestRenderAll();
    };

    const handleOpacityChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const val = parseFloat(e.target.value);
        setOpacity(val);
        if (logoObject && fabricCanvas) {
            logoObject.set('opacity', val);
            fabricCanvas.requestRenderAll();
        }
    };

    // Toggle Blend Mode
    const toggleBlendMode = () => {
        if (!logoObject || !fabricCanvas) return;
        const newMode = blendMode === "normal" ? "multiply" : "normal";
        setBlendMode(newMode);

        // Fabric uses 'globalCompositeOperation', multiply maps to 'multiply'
        // 'normal' maps to 'source-over' default
        const gco = newMode === "multiply" ? "multiply" : "source-over";
        logoObject.set('globalCompositeOperation', gco);
        fabricCanvas.requestRenderAll();
    };

    const handleAddToOrder = async () => {
        if (!logoObject || !fabricCanvas) {
            showToast("אנא העלה לוגו תחילה", "error");
            return;
        }

        setIsSubmitting(true);

        try {
            // 1. Prepare blobs
            const logoSrc = logoObject.toDataURL({ format: 'png' });
            const mockupSrc = fabricCanvas.toDataURL({ format: 'png', multiplier: 2 });

            const [logoBlob, mockupBlob] = await Promise.all([
                fetch(logoSrc).then(r => r.blob()),
                fetch(mockupSrc).then(r => r.blob())
            ]);

            // 2. Add to order via hook
            await addItem(
                {
                    product_title: product.title,
                    sku: product.sku_clean,
                    width: widthCm,
                    quantity: quantity,
                    logo_src: logoSrc,
                    mockup_src: mockupSrc
                },
                logoBlob,
                mockupBlob
            );

            showToast("המוצר נוסף לסל ההזמנה בהצלחה!", "success");
            if (onClose) onClose();

        } catch (e: any) {
            console.error(e);
            showToast("שגיאה בהוספת המוצר: " + e.message, "error");
        } finally {
            setIsSubmitting(false);
        }

    };

    return (
        <div className="flex flex-col gap-4 text-right" dir="rtl">
            <div className="flex items-center justify-between">
                <h3 className="text-xl font-bold text-gray-800 flex items-center gap-2">
                    <span className="text-2xl">🎨</span>
                    עורך הדמיה
                </h3>
            </div>

            <div className="flex flex-col lg:flex-row gap-6">
                {/* Editor Area */}
                <div className="flex-1 flex flex-col gap-4">
                    <div className="relative flex-[2] min-h-[500px] max-h-[70vh] overflow-hidden rounded-xl bg-gray-100 border border-gray-200 shadow-inner" ref={containerRef}>
                        <div className="absolute inset-0 flex items-center justify-center p-4">
                            <div className="relative">
                                <canvas ref={canvasRef} />
                                {selectedObjectPos && (
                                    <button
                                        onClick={removeLogo}
                                        className="absolute z-20 p-2 bg-red-600 text-white rounded-full shadow-lg hover:bg-red-700 transition transform -translate-x-1/2 -translate-y-1/2"
                                        style={{
                                            left: selectedObjectPos.x,
                                            top: selectedObjectPos.y
                                        }}
                                        title="מחק לוגו"
                                    >
                                        <X size={14} />
                                    </button>
                                )}
                            </div>
                        </div>

                        <div className="pointer-events-none absolute bottom-3 left-0 right-0 text-center">
                            <span className="inline-block bg-white/70 backdrop-blur px-3 py-1 rounded-full text-[10px] text-gray-600 shadow-sm border border-white/50">
                                המיקום והגודל להמחשה בלבד
                            </span>
                        </div>
                    </div>

                    {/* Image Selector Strip */}
                    {!readOnly && availableImages.length > 1 && (
                        <div className="flex flex-wrap gap-2 justify-center">
                            {availableImages.map((img, idx) => (
                                <button
                                    key={idx}
                                    onClick={() => setSelectedImageIndex(idx)}
                                    className={`relative flex-shrink-0 w-16 h-16 rounded-lg border-2 overflow-hidden transition ${selectedImageIndex === idx
                                        ? "border-blue-600 ring-2 ring-blue-100"
                                        : "border-transparent hover:border-gray-300 opacity-70 hover:opacity-100"
                                        }`}
                                >
                                    <img src={img} alt={`Variant ${idx}`} className="w-full h-full object-cover" />
                                </button>
                            ))}
                        </div>
                    )}
                </div>

                {/* Controls Panel */}
                {!readOnly && (
                    <div className="w-full lg:w-72 flex flex-col gap-4">
                        <div className="p-4 bg-gray-50 rounded-xl border border-gray-100 space-y-4">
                            <h4 className="font-bold text-gray-700 text-sm">פרטי הזמנה</h4>
                            <div className="grid grid-cols-2 gap-3">
                                <div className="space-y-1">
                                    <label className="text-xs text-gray-500 block">כמות</label>
                                    <input
                                        type="number"
                                        value={quantity}
                                        onChange={(e) => setQuantity(parseInt(e.target.value) || 0)}
                                        className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
                                        min="1"
                                    />
                                </div>
                                <div className="space-y-1">
                                    <label className="text-xs text-gray-500 block">רוחב (ס"מ)</label>
                                    <input
                                        type="number"
                                        step="0.1"
                                        value={widthCm}
                                        onChange={(e) => setWidthCm(parseFloat(e.target.value) || 0)}
                                        className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
                                        min="0.1"
                                    />
                                </div>
                            </div>
                        </div>

                        <div className="p-4 bg-gray-50 rounded-xl border border-gray-100 space-y-4">
                            <h4 className="font-bold text-gray-700 text-sm">ניהול לוגו</h4>
                            <label className="flex w-full cursor-pointer items-center justify-center gap-2 rounded-xl border-2 border-dashed border-blue-200 bg-white px-4 py-6 text-center hover:border-blue-400 hover:bg-blue-50 transition group">
                                <div className="flex flex-col items-center gap-1 group-hover:text-blue-600 text-gray-500">
                                    <Upload size={24} />
                                    <span className="text-sm font-medium">לחץ להעלאת לוגו</span>
                                </div>
                                <input type="file" accept="image/*" className="hidden" onChange={handleFileUpload} />
                            </label>

                            {logoObject && (
                                <div className="space-y-3 animate-in fade-in slide-in-from-top-2">
                                    {/* BG Removal & Blend Mode - Hidden for now */}
                                    {false && (
                                        <>
                                            <button
                                                onClick={handleRemoveBackground}
                                                disabled={isProcessingBg || (!isModelReady && isModelDownloading)}
                                                className="relative overflow-hidden w-full flex items-center justify-center gap-2 bg-white border border-gray-200 hover:bg-purple-50 hover:border-purple-200 text-gray-700 hover:text-purple-700 py-2 rounded-lg text-sm font-medium transition"
                                            >
                                                {(isProcessingBg || isModelDownloading) && (
                                                    <div
                                                        className="absolute bottom-0 left-0 top-0 bg-purple-100 transition-all duration-300 z-0"
                                                        style={{ width: `${progressPercent}%`, opacity: 0.5 }}
                                                    />
                                                )}
                                                <div className="relative z-10 flex items-center gap-2">
                                                    {(isProcessingBg || isModelDownloading) ? (
                                                        <span className="animate-spin">⏳</span>
                                                    ) : (
                                                        <Sparkles size={16} className="text-purple-500" />
                                                    )}
                                                    {isModelDownloading ? `מוריד מודל AI... (${progressPercent}%)` :
                                                        isProcessingBg ? (progressText || "מסיר רקע...") : "הסר רקע (AI)"}
                                                </div>
                                            </button>

                                            <button
                                                onClick={toggleBlendMode}
                                                className={`w-full flex items-center justify-center gap-2 border px-3 py-2 rounded-lg text-sm font-medium transition ${blendMode === "multiply"
                                                    ? "bg-blue-100 border-blue-300 text-blue-800"
                                                    : "bg-white border-gray-200 text-gray-600 hover:bg-gray-50"
                                                    }`}
                                            >
                                                {blendMode === "multiply" ? <Check size={16} /> : <div className="w-4" />}
                                                מצב כפל (שקוף ללבן)
                                            </button>
                                        </>
                                    )}

                                    <div className="space-y-1">
                                        <div className="flex justify-between text-xs text-gray-500">
                                            <span>שקיפות</span>
                                            <span>{Math.round(opacity * 100)}%</span>
                                        </div>
                                        <input
                                            type="range"
                                            min="0"
                                            max="1"
                                            step="0.1"
                                            value={opacity}
                                            onChange={handleOpacityChange}
                                            className="h-2 w-full cursor-pointer appearance-none rounded-lg bg-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                        />
                                    </div>

                                    <button
                                        onClick={removeLogo}
                                        className="w-full flex items-center justify-center gap-2 border border-red-200 bg-red-50 text-red-600 hover:bg-red-100 px-3 py-2 rounded-lg text-sm font-medium transition"
                                    >
                                        <X size={16} />
                                        מחק לוגו
                                    </button>
                                </div>
                            )}
                        </div>

                        <button
                            onClick={handleAddToOrder}
                            disabled={isSubmitting || !logoObject}
                            className="mt-auto w-full flex items-center justify-center gap-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white py-4 font-bold text-lg shadow-md hover:shadow-lg transition-transform hover:scale-[1.02] active:scale-95 disabled:opacity-50 disabled:scale-100"
                        >
                            {isSubmitting ? (
                                <span className="flex items-center gap-2">
                                    <RefreshCcw size={20} className="animate-spin" />
                                    מוסיף להזמנה...
                                </span>
                            ) : (
                                <>
                                    <Check size={20} />
                                    הוסף לסל ההזמנה
                                </>
                            )}
                        </button>
                    </div>
                )}
            </div>
        </div>
    );

}
