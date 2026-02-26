import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export interface PlaceholderFormProps {
  sectionId?: string;
  title?: string;
  children?: React.ReactNode;
  defaultValues?: any;
  onSave?: any;
  form?: any;
}

export const PlaceholderForm = ({ sectionId, title, children, defaultValues, onSave, form }: PlaceholderFormProps) => {
  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>{title || "Sección en desarrollo"}</CardTitle>
      </CardHeader>
      <CardContent>
        {children || (
          <div className="p-4 border rounded bg-muted/20 text-muted-foreground">
            Form configuration for {sectionId || "unknown section"}
          </div>
        )}
      </CardContent>
    </Card>
  );
};
