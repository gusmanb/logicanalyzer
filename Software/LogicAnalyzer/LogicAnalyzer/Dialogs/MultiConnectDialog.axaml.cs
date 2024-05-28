using Avalonia.Controls;
using LogicAnalyzer.Extensions;
using System;
using System.Collections.Generic;
using System.IO.Ports;

namespace LogicAnalyzer.Dialogs
{
    public partial class MultiConnectDialog : Window
    {
        string[]? connStrs;

        public string[]? ConnectionStrings{ get { return connStrs; } }
        CheckBox[] cks;
        ComboBox[] dbs;
        TextBlock[] tbs;
        public MultiConnectDialog()
        {
            InitializeComponent();
            FindControls();
            FillPorts();
            btnAccept.Click += BtnAccept_Click;
            btnCancel.Click += BtnCancel_Click;
        }

        private void BtnCancel_Click(object? sender, Avalonia.Interactivity.RoutedEventArgs e)
        {
            this.Close(false);
        }

        private async void BtnAccept_Click(object? sender, Avalonia.Interactivity.RoutedEventArgs e)
        {
            List<string> conns = new List<string>();

            string? connStr = dbs[0].SelectedItem?.ToString();

            if (connStr == null)
            {
                await this.ShowError("Error", "Master device is not selected.");
                return;
            }

            if (connStr == "Network")
                connStr = tbs[0].Text;

            conns.Add(connStr);

            for (int buc = 0; buc < 4; buc++)
            {
                if (cks[buc].IsChecked == true)
                {
                    connStr = dbs[buc + 1].SelectedItem?.ToString();

                    if (connStr == null)
                    {
                        await this.ShowError("Error", $"Slave device {buc + 1} is enabled but not selected.");
                        return;
                    }

                    if (connStr == "Network")
                        connStr = tbs[buc + 1].Text;

                    conns.Add(connStr);
                }
            }

            if (conns.Count < 2)
            {
                await this.ShowError("Error", $"No slave device selected.");
                return;
            }

            connStrs = conns.ToArray();

            this.Close(true);
        }

        void FindControls()
        {
            List<CheckBox> checks = new List<CheckBox>();
            List<ComboBox> drops = new List<ComboBox>();
            List<TextBlock> blocks = new List<TextBlock>();

            drops.Add(ddMaster);
            blocks.Add(tbMaster);

            for (int buc = 1; buc < 5; buc++)
            {
                checks.Add(this.FindControl<CheckBox>($"ckSlave{buc}"));
                drops.Add(this.FindControl<ComboBox>($"ddSlave{buc}"));
                blocks.Add(this.FindControl<TextBlock>($"tbSlave{buc}"));
            }

            foreach (var check in checks)
            {
                check.Checked += Check_Checked;
                check.Unchecked += Check_Unchecked;
            }

            foreach(var drop in drops)
                drop.SelectionChanged += Drop_SelectionChanged;

            cks = checks.ToArray();
            dbs = drops.ToArray();
            tbs = blocks.ToArray();
        }

        void FillPorts()
        {
            List<string> portNames = new List<string>();
            portNames.AddRange(SerialPort.GetPortNames());
            portNames.Add("Network");

            foreach (var dd in dbs)
                dd.Items = portNames.ToArray();
        }

        private async void Drop_SelectionChanged(object? sender, SelectionChangedEventArgs e)
        {
            var index = Array.IndexOf(dbs, sender);
            var value = dbs[index].SelectedItem?.ToString();

            if (value == null)
                tbs[index].Text = "";
            else
            {
                if(value == "Network")
                {
                    var dlg = new NetworkDialog();
                    var success = await dlg.ShowDialog<bool>(this);

                    if (!success)
                    {
                        dbs[index].SelectedItem = null;
                        tbs[index].Text = "";
                    }
                    else
                        tbs[index].Text = $"{dlg.Address}:{dlg.Port}";
                }
                else
                    tbs[index].Text = "";
            }
        }

        private void Check_Unchecked(object? sender, Avalonia.Interactivity.RoutedEventArgs e)
        {
            var index = Array.IndexOf(cks, sender) + 1;
            dbs[index].IsEnabled = false;
        }

        private void Check_Checked(object? sender, Avalonia.Interactivity.RoutedEventArgs e)
        {
            var index = Array.IndexOf(cks, sender) + 1;
            dbs[index].IsEnabled = true;
        }
    }
}
