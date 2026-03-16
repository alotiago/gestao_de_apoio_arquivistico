import type { ElementType } from "react";

type DashboardStatCardProps = {
  title: string;
  value: string;
  description: string;
  icon: ElementType;
};

export function DashboardStatCard({
  title,
  value,
  description,
  icon: Icon,
}: DashboardStatCardProps) {
  return (
    <div className="rounded-xl border bg-background p-6 shadow-sm">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-muted-foreground">{title}</p>
          <p className="mt-1 text-3xl font-bold text-foreground">{value}</p>
          <p className="mt-1 text-xs text-muted-foreground">{description}</p>
        </div>
        <div className="rounded-lg bg-primary/10 p-3">
          <Icon className="h-6 w-6 text-primary" />
        </div>
      </div>
    </div>
  );
}

type DashboardPlaceholderChartCardProps = {
  title: string;
  description: string;
  icon: ElementType;
};

export function DashboardPlaceholderChartCard({
  title,
  description,
  icon: Icon,
}: DashboardPlaceholderChartCardProps) {
  return (
    <div className="rounded-xl border bg-background p-6 shadow-sm">
      <h3 className="mb-4 text-lg font-semibold text-foreground">{title}</h3>
      <div className="flex h-64 items-center justify-center text-muted-foreground">
        <div className="text-center">
          <Icon className="mx-auto mb-2 h-12 w-12 opacity-50" />
          <p>{description}</p>
        </div>
      </div>
    </div>
  );
}
