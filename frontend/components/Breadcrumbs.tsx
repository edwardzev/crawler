import { ChevronRight } from "lucide-react";
import Link from "next/link";
import { Fragment } from "react";

interface BreadcrumbsProps {
    items: {
        label: string;
        href: string;
    }[];
}

export function Breadcrumbs({ items }: BreadcrumbsProps) {
    return (
        <nav className="flex items-center text-sm text-gray-500">
            <Link href="/" className="hover:text-gray-900">
                בית
            </Link>
            {items.map((item, index) => (
                <Fragment key={item.href}>
                    <ChevronRight className="mx-2 h-4 w-4" />
                    <Link
                        href={item.href}
                        className={index === items.length - 1 ? "font-medium text-gray-900 pointer-events-none" : "hover:text-gray-900"}
                    >
                        {item.label}
                    </Link>
                </Fragment>
            ))}
        </nav>
    );
}
