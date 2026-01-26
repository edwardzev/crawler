"use client";

import React, { useState } from 'react';
import { useOrder } from '@/lib/hooks/useOrder';
import { useToast } from "@/lib/contexts/ToastContext";
import { ConfirmModal } from "@/components/ui/ConfirmModal";
import { X, ShoppingBag, Send, Calendar, FileText, CheckCircle2 } from 'lucide-react';
import { FinalizeOrderForm } from './FinalizeOrderForm';

export function OrderSummary() {
    const { orderState, resetOrder } = useOrder();
    const { showToast } = useToast();
    const [showFinalForm, setShowFinalForm] = useState(false);
    const [isConfirmOpen, setIsConfirmOpen] = useState(false);

    if (!orderState.order_id || orderState.items.length === 0) return null;

    return (
        <div className="fixed bottom-6 left-6 z-40 w-80 max-h-[80vh] flex flex-col bg-white rounded-2xl shadow-2xl border border-gray-100 overflow-hidden animate-in slide-in-from-bottom-10 duration-300" dir="rtl">
            {/* Header */}
            <div className="bg-blue-600 p-4 text-white flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <ShoppingBag size={20} />
                    <h3 className="font-bold text-sm">סיכום הזמנה #{orderState.order_id.slice(-6)}</h3>
                </div>
                <button
                    onClick={() => setIsConfirmOpen(true)}
                    className="text-blue-100 hover:text-white transition"
                    title="אפס הזמנה"
                >
                    <X size={18} />
                </button>
            </div>

            <ConfirmModal
                isOpen={isConfirmOpen}
                title="איפוס הזמנה"
                message="האם אתה בטוח שברצונך לאפס את ההזמנה? כל הפריטים יימחקו."
                onConfirm={() => {
                    resetOrder();
                    setIsConfirmOpen(false);
                    showToast("ההזמנה אופסה בהצלחה", "info");
                }}
                onCancel={() => setIsConfirmOpen(false)}
                isDestructive={true}
                confirmText="אפס הזמנה"
            />

            {/* Items List */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50/50">
                {orderState.items.map((item) => (
                    <div key={item.id} className="bg-white p-3 rounded-xl border border-gray-100 shadow-sm space-y-2">
                        <div className="flex gap-3">
                            <div className="w-12 h-12 bg-gray-100 rounded-lg overflow-hidden flex-shrink-0 border border-gray-50">
                                <img src={item.logo_src} alt="Logo" className="w-full h-full object-contain p-1" />
                            </div>
                            <div className="flex-1 min-w-0">
                                <h4 className="text-xs font-bold text-gray-800 truncate">{item.product_title}</h4>
                                <p className="text-[10px] text-gray-500">מק"ט: {item.sku}</p>
                            </div>
                            <div className="text-[10px] font-bold bg-blue-50 text-blue-600 px-2 py-1 rounded-md h-fit">
                                סלוט {item.slot_index}
                            </div>
                        </div>
                        <div className="flex justify-between items-center pt-2 border-t border-gray-50 text-[10px]">
                            <div className="flex gap-3 text-gray-600 font-medium">
                                <span>כמות: <span className="text-gray-900">{item.quantity}</span></span>
                                <span>רוחב: <span className="text-gray-900">{item.width} ס"מ</span></span>
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {/* Footer Actions */}
            <div className="p-4 bg-white border-t border-gray-100 space-y-3">
                <div className="flex justify-between text-xs mb-1">
                    <span className="text-gray-500">סה"כ פריטים:</span>
                    <span className="font-bold">{orderState.items.length}</span>
                </div>

                <button
                    onClick={() => setShowFinalForm(true)}
                    className="w-full flex items-center justify-center gap-2 bg-green-500 hover:bg-green-600 text-white py-3 rounded-xl font-bold text-sm shadow-md transition-all active:scale-95"
                >
                    <Send size={16} />
                    שלח הזמנה לביצוע
                </button>
            </div>

            {/* Finalization Modal */}
            {showFinalForm && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in duration-200">
                    <div className="relative w-full max-w-lg bg-white rounded-3xl shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200">
                        <div className="p-6">
                            <div className="flex justify-between items-center mb-6">
                                <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
                                    <CheckCircle2 className="text-green-500" />
                                    סיום הזמנה
                                </h2>
                                <button
                                    onClick={() => setShowFinalForm(false)}
                                    className="p-2 bg-gray-100 rounded-full hover:bg-gray-200 transition"
                                >
                                    <X size={20} />
                                </button>
                            </div>

                            <FinalizeOrderForm onSuccess={() => setShowFinalForm(false)} />
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
