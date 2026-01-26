"use client";

import React, { useState } from 'react';
import { useOrder } from '@/lib/hooks/useOrder';
import { useToast } from "@/lib/contexts/ToastContext";
import { Calendar, FileText, Check, Loader2, AlertCircle } from 'lucide-react';

interface Props {
    onSuccess?: () => void;
}

export function FinalizeOrderForm({ onSuccess }: Props) {
    const { orderState, finalizeOrder } = useOrder();
    const { showToast } = useToast();
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const [formData, setFormData] = useState({
        job_name: '',
        deadline: '',
        method: 'DTF',
        notes: '',
        final_check: false
    });

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!formData.final_check) {
            setError("חובה לאשר את פרטי ההזמנה");
            return;
        }

        setIsSubmitting(true);
        setError(null);

        try {
            await finalizeOrder({
                job_name: formData.job_name,
                deadline: formData.deadline,
                method: formData.method,
                notes: formData.notes,
                final_check: formData.final_check
            });

            showToast("ההזמנה נשלחה בהצלחה!", "success");
            if (onSuccess) onSuccess();
        } catch (e: any) {
            console.error(e);
            setError(e.message || "שגיאה בשליחת ההזמנה");
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-6 text-right" dir="rtl">
            {error && (
                <div className="bg-red-50 border border-red-100 p-4 rounded-xl flex items-center gap-3 text-red-600 animate-in fade-in slide-in-from-top-2">
                    <AlertCircle size={20} />
                    <p className="text-sm font-medium">{error}</p>
                </div>
            )}

            <div className="space-y-4">
                {/* Job Name */}
                <div className="space-y-1">
                    <label className="text-sm font-bold text-gray-700 block">שם העבודה / לקוח</label>
                    <div className="relative">
                        <input
                            type="text"
                            required
                            value={formData.job_name}
                            onChange={(e) => setFormData(prev => ({ ...prev, job_name: e.target.value }))}
                            className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all outline-none"
                            placeholder="למשל: אירוע חברה - מאי 2024"
                        />
                    </div>
                </div>

                {/* Deadline */}
                <div className="space-y-1">
                    <label className="text-sm font-bold text-gray-700 block">תאריך אספקה מבוקש</label>
                    <div className="relative">
                        <div className="absolute inset-y-0 right-4 flex items-center pointer-events-none text-gray-400">
                            <Calendar size={18} />
                        </div>
                        <input
                            type="date"
                            required
                            value={formData.deadline}
                            onChange={(e) => setFormData(prev => ({ ...prev, deadline: e.target.value }))}
                            className="w-full pr-12 pl-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all outline-none"
                        />
                    </div>
                </div>

                {/* Method */}
                <div className="space-y-1">
                    <label className="text-sm font-bold text-gray-700 block">שיטת הדפסה</label>
                    <div className="relative">
                        <select
                            value={formData.method}
                            onChange={(e) => setFormData(prev => ({ ...prev, method: e.target.value }))}
                            className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all outline-none appearance-none cursor-pointer"
                        >
                            <option value="DTF">DTF</option>
                            <option value="UV">UV</option>
                            <option value="DTF – UV">DTF – UV</option>
                        </select>
                    </div>
                </div>

                {/* Notes */}
                <div className="space-y-1">
                    <label className="text-sm font-bold text-gray-700 block">הערות כלליות להזמנה</label>
                    <div className="relative">
                        <div className="absolute top-3 right-4 pointer-events-none text-gray-400">
                            <FileText size={18} />
                        </div>
                        <textarea
                            value={formData.notes}
                            onChange={(e) => setFormData(prev => ({ ...prev, notes: e.target.value }))}
                            className="w-full pr-12 pl-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all outline-none min-h-[100px]"
                            placeholder="הערות נוספות למחלקת הגרפיקה או הייצור..."
                        />
                    </div>
                </div>

                {/* Final Check */}
                <label className="flex items-start gap-3 cursor-pointer group">
                    <div className="relative flex items-center pt-1">
                        <input
                            type="checkbox"
                            required
                            checked={formData.final_check}
                            onChange={(e) => setFormData(prev => ({ ...prev, final_check: e.target.checked }))}
                            className="peer sr-only"
                        />
                        <div className="w-5 h-5 border-2 border-gray-300 rounded-md peer-checked:bg-blue-600 peer-checked:border-blue-600 transition-all"></div>
                        <Check className="absolute text-white scale-0 peer-checked:scale-100 transition-transform duration-200 left-[2px]" size={16} />
                    </div>
                    <span className="text-sm text-gray-600 leading-tight group-hover:text-gray-900 transition-colors">
                        מאשר/ת כי בדקתי את כל פרטי ההזמנה, המיקומים והכמויות.
                    </span>
                </label>
            </div>

            <button
                type="submit"
                disabled={isSubmitting || !formData.final_check}
                className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:bg-gray-300 text-white py-4 rounded-2xl font-bold text-lg shadow-lg hover:shadow-xl transition-all active:scale-[0.98]"
            >
                {isSubmitting ? (
                    <>
                        <Loader2 className="animate-spin" />
                        שולח הזמנה...
                    </>
                ) : (
                    <>
                        שלח הזמנה סופית
                    </>
                )}
            </button>
        </form>
    );
}
