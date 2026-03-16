type ModulePageShellProps = {
  title: string;
  description: string;
  placeholderTitle: string;
  placeholderSubtitle: string;
  actionLabel?: string;
};

export function ModulePageShell({
  title,
  description,
  placeholderTitle,
  placeholderSubtitle,
  actionLabel,
}: ModulePageShellProps) {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">{title}</h1>
          <p className="text-muted-foreground">{description}</p>
        </div>
        {actionLabel ? (
          <button
            type="button"
            className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
          >
            {actionLabel}
          </button>
        ) : null}
      </div>

      <div className="rounded-xl border bg-background p-12 text-center text-muted-foreground shadow-sm">
        <p className="text-lg text-foreground">{placeholderTitle}</p>
        <p className="mt-2 text-sm">{placeholderSubtitle}</p>
      </div>
    </div>
  );
}
