'use client'

import React, { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Slider } from '@/components/ui/slider'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from '@/components/ui/select'

interface InteractiveComponentConfig {
  type: string;
  config: any;
  field_name?: string;
}

interface InteractivePromptsProps {
  component: InteractiveComponentConfig;
  onSelection: (value: any, displayText: string) => void;
}

export default function InteractivePrompts({ component, onSelection }: InteractivePromptsProps) {
  const { type, config } = component;

  const handleSelection = (value: any, displayText: string) => {
    onSelection(value, displayText);
  };

  switch (type) {
    case 'buttons':
      return <ButtonGroupPrompt config={config} onSelection={handleSelection} />;
    case 'slider':
      return <SliderPrompt config={config} onSelection={handleSelection} />;
    case 'range_slider':
      return <RangeSliderPrompt config={config} onSelection={handleSelection} />;
    case 'toggle':
      return <TogglePrompt config={config} onSelection={handleSelection} />;
    case 'checklist':
      return <ChecklistPrompt config={config} onSelection={handleSelection} />;
    case 'dropdown':
      return <DropdownPrompt config={config} onSelection={handleSelection} />;
    default:
      return null;
  }
}

// Button Group Component
function ButtonGroupPrompt({ config, onSelection }: { config: any; onSelection: (value: any, displayText: string) => void }) {
  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 my-3">
      <Label className="text-sm font-medium text-gray-900 mb-3 block">{config.title}</Label>
      <div className="grid grid-cols-2 gap-2">
        {config.options.map((option: any, index: number) => {
          // Use custom response template if provided, otherwise use option's response_text or fallback
          const displayText = option.response_text || 
                            (config.response_template ? config.response_template.replace('{value}', option.label) : null) ||
                            `${option.label}`;
          
          return (
            <Button
              key={index}
              variant="outline"
              className="h-12 text-sm font-medium hover:bg-blue-100 hover:border-blue-300"
              onClick={() => onSelection(option.value, displayText)}
            >
              {option.label}
            </Button>
          );
        })}
      </div>
    </div>
  );
}

// Slider Component using shadcn/ui
function SliderPrompt({ config, onSelection }: { config: any; onSelection: (value: any, displayText: string) => void }) {
  const [value, setValue] = useState([config.default || config.min]);

  const handleValueChange = (newValue: number[]) => {
    setValue(newValue);
  };

  const handleSubmit = () => {
    const selectedValue = value[0];
    const displayText = `I need ${selectedValue}${config.suffix || ''}`;
    onSelection(selectedValue, displayText);
  };

  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 my-3">
      <Label className="text-sm font-medium text-gray-900 mb-4 block">{config.title}</Label>
      <div className="space-y-4">
        <div className="px-2">
          <Slider
            value={value}
            onValueChange={handleValueChange}
            min={config.min}
            max={config.max}
            step={config.step || 1}
            className="w-full"
          />
          <div className="flex justify-between text-xs text-gray-600 mt-2">
            <span>{config.min}{config.suffix || ''}</span>
            <span className="font-medium text-blue-600 text-sm">
              {value[0]}{config.suffix || ''}
            </span>
            <span>{config.max}{config.suffix || ''}</span>
          </div>
        </div>
        <Button 
          onClick={handleSubmit}
          className="w-full bg-blue-600 hover:bg-blue-700"
        >
          Select {value[0]}{config.suffix || ''}
        </Button>
      </div>
    </div>
  );
}

// Range Slider Component using shadcn/ui
function RangeSliderPrompt({ config, onSelection }: { config: any; onSelection: (value: any, displayText: string) => void }) {
  const [values, setValues] = useState([
    config.default_min || config.min,
    config.default_max || config.max
  ]);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const handleValueChange = (newValues: number[]) => {
    setValues(newValues);
  };

  const handleSubmit = () => {
    const displayText = `My budget is between ${formatCurrency(values[0])} and ${formatCurrency(values[1])}`;
    onSelection({ min: values[0], max: values[1] }, displayText);
  };

  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 my-3">
      <Label className="text-sm font-medium text-gray-900 mb-4 block">{config.title}</Label>
      <div className="space-y-4">
        <div className="px-2">
          <Slider
            value={values}
            onValueChange={handleValueChange}
            min={config.min}
            max={config.max}
            step={config.step || 1000}
            className="w-full"
          />
          <div className="flex justify-between text-xs text-gray-600 mt-2">
            <span>{formatCurrency(config.min)}</span>
            <div className="flex items-center gap-2 font-medium text-blue-600 text-sm">
              <span>{formatCurrency(values[0])}</span>
              <span className="text-gray-400">to</span>
              <span>{formatCurrency(values[1])}</span>
            </div>
            <span>{formatCurrency(config.max)}</span>
          </div>
        </div>
        <Button 
          onClick={handleSubmit}
          className="w-full bg-blue-600 hover:bg-blue-700"
        >
          Select {formatCurrency(values[0])} - {formatCurrency(values[1])}
        </Button>
      </div>
    </div>
  );
}

// Toggle Component
function TogglePrompt({ config, onSelection }: { config: any; onSelection: (value: any, displayText: string) => void }) {
  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 my-3">
      <Label className="text-sm font-medium text-gray-900 mb-3 block">{config.title}</Label>
      <div className="space-y-2">
        {config.options.map((option: any, index: number) => {
          // Use custom response_text if provided, otherwise use the label
          const displayText = option.response_text || option.label;
          
          return (
            <Button
              key={index}
              variant="outline"
              className="w-full justify-start h-12 text-sm font-medium hover:bg-blue-100 hover:border-blue-300"
              onClick={() => onSelection(option.value, displayText)}
            >
              {option.label}
            </Button>
          );
        })}
      </div>
    </div>
  );
}

// Checklist Component (Multi-select with checkboxes)
function ChecklistPrompt({ config, onSelection }: { config: any; onSelection: (value: any, displayText: string) => void }) {
  const [selectedItems, setSelectedItems] = useState<string[]>([]);

  const handleCheckboxChange = (optionValue: string, checked: boolean) => {
    if (checked) {
      setSelectedItems(prev => [...prev, optionValue]);
    } else {
      setSelectedItems(prev => prev.filter(item => item !== optionValue));
    }
  };

  const handleSubmit = () => {
    if (selectedItems.length === 0) return;
    
    const selectedLabels = config.options
      .filter((option: any) => selectedItems.includes(option.value))
      .map((option: any) => option.label);
    
    const displayText = selectedLabels.length === 1 
      ? `I need ${selectedLabels[0].toLowerCase()}`
      : `I need: ${selectedLabels.join(', ').toLowerCase()}`;
    
    onSelection(selectedItems, displayText);
  };

  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 my-3">
      <Label className="text-sm font-medium text-gray-900 mb-3 block">{config.title}</Label>
      <div className="space-y-3 mb-4">
        {config.options.map((option: any, index: number) => (
          <div key={index} className="flex items-center space-x-3">
            <Checkbox
              id={`checkbox-${index}`}
              checked={selectedItems.includes(option.value)}
              onCheckedChange={(checked) => handleCheckboxChange(option.value, checked as boolean)}
            />
            <Label 
              htmlFor={`checkbox-${index}`}
              className="text-sm font-normal text-gray-700 cursor-pointer"
            >
              {option.label}
            </Label>
          </div>
        ))}
      </div>
      <Button 
        onClick={handleSubmit}
        disabled={selectedItems.length === 0}
        className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
      >
        Select {selectedItems.length} item{selectedItems.length !== 1 ? 's' : ''}
      </Button>
    </div>
  );
}

// Dropdown Component (Single select from larger list)
function DropdownPrompt({ config, onSelection }: { config: any; onSelection: (value: any, displayText: string) => void }) {
  const [selectedValue, setSelectedValue] = useState<string>('');

  const handleValueChange = (value: string) => {
    setSelectedValue(value);
    
    // Find the selected option to get the label
    const selectedOption = config.options.find((option: any) => option.value === value);
    if (selectedOption) {
      const displayText = config.response_template 
        ? config.response_template.replace('{value}', selectedOption.label)
        : `I selected ${selectedOption.label}`;
      
      onSelection(value, displayText);
    }
  };

  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 my-3">
      <Label className="text-sm font-medium text-gray-900 mb-3 block">{config.title}</Label>
      <Select onValueChange={handleValueChange} value={selectedValue}>
        <SelectTrigger className="w-full bg-white">
          <SelectValue placeholder={config.placeholder || "Select an option..."} />
        </SelectTrigger>
        <SelectContent>
          {config.options.map((option: any, index: number) => (
            <SelectItem key={index} value={option.value}>
              {option.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
