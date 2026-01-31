"use client";

import { useState, useEffect } from 'react';
import { OrderState, OrderItem } from '@/lib/types';
import { v4 as uuidv4 } from 'uuid';

const STORAGE_KEY = 'harmonic_ride_order';

export function useOrder() {
    const [orderState, setOrderState] = useState<OrderState>({
        order_id: null,
        items: [],
        used_slots: []
    });

    const [isLoaded, setIsLoaded] = useState(false);

    useEffect(() => {
        const saved = localStorage.getItem(STORAGE_KEY);
        if (saved) {
            try {
                setOrderState(JSON.parse(saved));
            } catch (e) {
                console.error("Failed to load order from storage", e);
            }
        }
        setIsLoaded(true);
    }, []);

    useEffect(() => {
        if (isLoaded) {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(orderState));
        }
    }, [orderState, isLoaded]);

    const getNextSlot = () => {
        for (let i = 1; i <= 5; i++) {
            if (!orderState.used_slots.includes(i)) return i;
        }
        return null;
    };

    const createOrder = async () => {
        const res = await fetch('/api/order/create', { method: 'POST' });
        if (!res.ok) throw new Error("Failed to create order");
        const { order_id } = await res.json();

        setOrderState(prev => ({
            ...prev,
            order_id
        }));

        return order_id;
    };

    const addItem = async (itemData: Omit<OrderItem, 'slot_index' | 'id'>, logoBlob: Blob, mockupBlob: Blob) => {
        let currentOrderId = orderState.order_id;

        if (!currentOrderId) {
            currentOrderId = await createOrder();
        }

        const slot = getNextSlot();
        if (slot === null) {
            throw new Error("Order is full. Maximum 5 prints per order.");
        }

        const formData = new FormData();
        formData.append("order_id", currentOrderId || "");
        formData.append("slot_index", slot.toString());
        formData.append("quantity", itemData.quantity.toString());
        formData.append("width", itemData.width.toString());
        formData.append("logo", logoBlob, "logo.png");
        formData.append("mockup", mockupBlob, "mockup.png");
        formData.append("product_title", itemData.product_title);
        formData.append("sku", itemData.sku);
        
        // Add variant data if present
        if (itemData.variant) {
            formData.append("variant_type", itemData.variant.type);
            formData.append("variant_value", itemData.variant.value);
            formData.append("variant_label", itemData.variant.label);
        }

        const res = await fetch('/api/order/add-item', {
            method: 'POST',
            body: formData
        });

        if (!res.ok) throw new Error("Failed to add item to order");

        const newItem: OrderItem = {
            ...itemData,
            id: uuidv4(),
            slot_index: slot
        };

        setOrderState(prev => ({
            ...prev,
            items: [...prev.items, newItem],
            used_slots: [...prev.used_slots, slot]
        }));

        return newItem;
    };

    const finalizeOrder = async (finalData: { job_name: string, deadline: string, method: string, notes: string, final_check: boolean }) => {
        if (!orderState.order_id) throw new Error("No active order");

        const res = await fetch('/api/order/finalize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                order_id: orderState.order_id,
                ...finalData
            })
        });

        if (!res.ok) throw new Error("Failed to finalize order");

        // Clear local order on success
        const resetState = {
            order_id: null,
            items: [],
            used_slots: []
        };
        setOrderState(resetState);
        localStorage.removeItem(STORAGE_KEY);

        return true;
    };

    const resetOrder = () => {
        setOrderState({ order_id: null, items: [], used_slots: [] });
        localStorage.removeItem(STORAGE_KEY);
    };

    return {
        orderState,
        addItem,
        finalizeOrder,
        resetOrder,
        isLoaded,
        getNextSlot
    };
}
