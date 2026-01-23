"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { CategoryNode } from "@/lib/types";
import { cn } from "@/lib/utils";
import { ChevronDown, ChevronRight } from "lucide-react";
import { useState } from "react";

interface SidebarProps {
    tree: CategoryNode;
}

export function Sidebar({ tree }: SidebarProps) {
    return (
        <aside className="w-full shrink-0 md:w-64">
            <div className="sticky top-20">
                <h2 className="mb-4 text-lg font-bold">קטגוריות</h2>
                <nav className="text-sm">
                    <ul className="space-y-1">
                        {tree.children.map((child) => (
                            <CategoryItem key={child.slug} node={child} parentPath="/c" />
                        ))}
                    </ul>
                </nav>
            </div>
        </aside>
    );
}

function CategoryItem({
    node,
    parentPath,
}: {
    node: CategoryNode;
    parentPath: string;
}) {
    const pathname = usePathname();
    const currentPath = `${parentPath}/${node.slug}`;
    const isActive = pathname === currentPath || pathname.startsWith(`${currentPath}/`);
    const hasChildren = node.children && node.children.length > 0;

    // Auto-expand if active or any child is active
    const [isOpen, setIsOpen] = useState(isActive);

    // If node has no products and no children, skip? 
    // No, maybe it's a placeholder. But count should guide us.

    return (
        <li>
            <div className="flex items-center justify-between rounded-md hover:bg-gray-50">
                <Link
                    href={currentPath}
                    className={cn(
                        "flex-1 px-3 py-2 transition-colors",
                        isActive ? "font-bold text-blue-600 bg-blue-50" : "text-gray-700"
                    )}
                >
                    {node.name}
                    {node.count > 0 && (
                        <span className="mr-2 text-xs text-gray-400">({node.count})</span>
                    )}
                </Link>
                {hasChildren && (
                    <button
                        onClick={() => setIsOpen(!isOpen)}
                        className="p-2 text-gray-400 hover:text-gray-600"
                    >
                        {isOpen ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                    </button>
                )}
            </div>

            {hasChildren && isOpen && (
                <ul className="mr-4 mt-1 border-r border-gray-200 pr-2 space-y-1">
                    {node.children.map((child) => (
                        <CategoryItem
                            key={child.slug}
                            node={child}
                            parentPath={currentPath}
                        />
                    ))}
                </ul>
            )}
        </li>
    );
}
