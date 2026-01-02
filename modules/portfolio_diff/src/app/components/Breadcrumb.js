"use client";

import Link from "next/link";
import { Home } from "lucide-react";
import PropTypes from "prop-types";

export default function Breadcrumb({
  items = [],
  homeHref = "/",
  homeLabel = "Dashboard",
  className = "",
}) {
  const wrapCls = `mb-4 ${className}`.trim();

  return (
    <nav className={wrapCls} aria-label="Breadcrumb">
      <ol className="flex items-center text-sm text-gray-600">
        {/* Home */}
        <li className="flex items-center">
          <Link
            href={homeHref}
            className="flex items-center gap-1 text-gray-900 hover:text-blue-600"
          >
            <Home className="h-4 w-4" />
            {homeLabel}
          </Link>
        </li>

        {/* Trail */}
        {items.map((item, idx) => {
          const isLast = idx === items.length - 1;
          return (
            <li key={`${item.label}-${idx}`} className="flex items-center">
              <span className="mx-2 text-gray-400">/</span>
              {item.href && !isLast ? (
                <Link
                  href={item.href}
                  className="hover:text-gray-900 max-w-[200px] truncate"
                >
                  {item.label}
                </Link>
              ) : (
                <span
                  className={`max-w-[240px] truncate ${
                    isLast ? "text-gray-900 font-medium" : "text-gray-700"
                  }`}
                  {...(isLast ? { "aria-current": "page" } : {})}
                >
                  {item.label}
                </span>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

Breadcrumb.propTypes = {
  items: PropTypes.arrayOf(
    PropTypes.shape({
      label: PropTypes.string.isRequired,
      href: PropTypes.string,
    })
  ),
  homeHref: PropTypes.string,
  homeLabel: PropTypes.string,
  className: PropTypes.string,
};
