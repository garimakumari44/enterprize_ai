"use client";

import { useEffect, useState } from "react";

import {
  Check,
  Edit3,
  X,
  MessageSquare,
  AlertTriangle,
} from "lucide-react";

import { Card } from "./ui/Card";
import { Button } from "./ui/Button";
import { ConfidenceBadge } from "./ui/ConfidenceBadge";
import { IconByName } from "./ui/IconByName";

import { typeIcon, typeColors } from "../../../lib/helpers";

export type HumanReviewItem = {
  id: string;
  documentName: string;
  type: string;
  confidence: number;
  issue: string;
  reason: string;
};

type HumanReviewPageProps = {
  reviewItems?: HumanReviewItem[];
  loading?: boolean;

  onApprove?: (id: string) => void;
  onReject?: (id: string) => void;
  onEdit?: (id: string) => void;
  onFeedback?: (id: string) => void;
  onApproveAll?: (ids: string[]) => void;
};

const EMPTY_REVIEW_ITEMS: HumanReviewItem[] = [];

/**
 * Safely get a value from a Record whose keys are a restricted union.
 *
 * This prevents TypeScript errors when the incoming document type
 * is a general string instead of the specific DocType union.
 */
function getRecordValue(
  record: Record<string, string>,
  key: string,
  fallback: string,
): string {
  return record[key] ?? fallback;
}

export function HumanReviewPage({
  reviewItems = EMPTY_REVIEW_ITEMS,
  loading = false,
  onApprove,
  onReject,
  onEdit,
  onFeedback,
  onApproveAll,
}: HumanReviewPageProps) {
  const [items, setItems] =
    useState<HumanReviewItem[]>(reviewItems);

  useEffect(() => {
    setItems(reviewItems);
  }, [reviewItems]);

  const approveItem = (id: string) => {
    setItems((previous) =>
      previous.filter((item) => item.id !== id),
    );

    onApprove?.(id);
  };

  const rejectItem = (id: string) => {
    setItems((previous) =>
      previous.filter((item) => item.id !== id),
    );

    onReject?.(id);
  };

  const approveAll = () => {
    const ids = items.map((item) => item.id);

    setItems([]);

    onApproveAll?.(ids);
  };

  const editItem = (id: string) => {
    onEdit?.(id);
  };

  const giveFeedback = (id: string) => {
    onFeedback?.(id);
  };

  if (loading) {
    return (
      <div className="space-y-3 animate-fade-in">
        {Array.from({ length: 4 }).map((_, index) => (
          <Card
            key={index}
            className="h-36 animate-pulse bg-slate-100 dark:bg-slate-800"
          >
            <div className="h-full w-full" />
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-4 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <AlertTriangle
            size={16}
            className="text-amber-500"
          />

          <span className="text-sm text-slate-600 dark:text-slate-400">
            {items.length} documents awaiting review
          </span>
        </div>

        <Button
          variant="secondary"
          size="sm"
          onClick={approveAll}
          disabled={items.length === 0}
        >
          <Check size={14} />
          Approve all
        </Button>
      </div>

      {/* Review items */}
      <div className="space-y-3">
        {items.map((item) => {
          /*
           * item.type is a general string.
           *
           * typeIcon/typeColors are Record<DocType, string>,
           * so we cannot directly do:
           *
           * typeIcon[item.type]
           *
           * Instead, convert the Record to a generic string-keyed
           * lookup for this UI boundary and provide fallbacks.
           */
          const iconName = getRecordValue(
            typeIcon as Record<string, string>,
            item.type,
            "FileText",
          );

          const iconColor = getRecordValue(
            typeColors as Record<string, string>,
            item.type,
            "text-slate-500",
          );

          return (
            <Card
              key={item.id}
              className="p-5"
            >
              <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                {/* Document information */}
                <div className="flex items-start gap-3">
                  <div className="grid h-10 w-10 shrink-0 place-items-center rounded-lg bg-gradient-to-br from-amber-50 to-orange-50 dark:from-amber-500/10 dark:to-orange-500/10">
                    <IconByName
                      name={iconName}
                      size={18}
                      className={iconColor}
                    />
                  </div>

                  <div>
                    <div className="text-sm font-semibold text-slate-800 dark:text-white">
                      {item.documentName}
                    </div>

                    <div className="mt-1 flex items-center gap-2">
                      <span className="text-xs text-slate-400">
                        AI Confidence
                      </span>

                      <ConfidenceBadge
                        value={item.confidence}
                        showBar
                      />
                    </div>
                  </div>
                </div>

                {/* Issue */}
                <div className="flex-1 lg:max-w-md">
                  <div className="flex items-center gap-2">
                    <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-amber-700 dark:bg-amber-500/15 dark:text-amber-400">
                      Issue
                    </span>

                    <span className="text-sm font-medium text-slate-800 dark:text-slate-200">
                      {item.issue}
                    </span>
                  </div>

                  <p className="mt-2 text-xs leading-relaxed text-slate-500 dark:text-slate-400">
                    {item.reason}
                  </p>
                </div>
              </div>

              {/* Actions */}
              <div className="mt-4 flex items-center gap-2 border-t border-slate-100 pt-4 dark:border-slate-800">
                <Button
                  size="sm"
                  onClick={() => approveItem(item.id)}
                >
                  <Check size={14} />
                  Approve
                </Button>

                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => editItem(item.id)}
                >
                  <Edit3 size={14} />
                  Edit
                </Button>

                <Button
                  variant="danger"
                  size="sm"
                  onClick={() => rejectItem(item.id)}
                >
                  <X size={14} />
                  Reject
                </Button>

                <Button
                  variant="ghost"
                  size="sm"
                  className="ml-auto"
                  onClick={() => giveFeedback(item.id)}
                >
                  <MessageSquare size={14} />
                  Feedback
                </Button>
              </div>
            </Card>
          );
        })}

        {/* Empty state */}
        {items.length === 0 && (
          <Card className="py-16 text-center">
            <Check
              size={36}
              className="mx-auto text-emerald-500"
            />

            <p className="mt-3 text-sm font-medium text-slate-700 dark:text-slate-200">
              All caught up!
            </p>

            <p className="mt-1 text-xs text-slate-400">
              No documents pending review
            </p>
          </Card>
        )}
      </div>
    </div>
  );
}