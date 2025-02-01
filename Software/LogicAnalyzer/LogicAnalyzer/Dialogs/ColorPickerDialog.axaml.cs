using Avalonia;
using Avalonia.Controls;
using Avalonia.Interactivity;
using Avalonia.Markup.Xaml;
using Avalonia.Media;
using System;

namespace LogicAnalyzer;

public partial class ColorPickerDialog : Window
{
    public Color PickerColor { get { return clrView.Color;  } set { clrView.Color = value; } }
    public ColorPickerDialog()
    {
        InitializeComponent();
        clrView.Palette = new MaterialColorPalette();
        btnAccept.Click += BtnAccept_Click;
        btnCancel.Click += BtnCancel_Click;
    }

    private void BtnCancel_Click(object? sender, RoutedEventArgs e)
    {
        this.Close((Color?)null);
    }

    private void BtnAccept_Click(object? sender, RoutedEventArgs e)
    {
        this.Close(PickerColor);
    }
}