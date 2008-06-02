
#include <QtGui>
#include <qfiledialog.h>

#include "ImportWorkspaceDlg.h"

ImportWorkspaceDlg::ImportWorkspaceDlg(QWidget *parent, int num) : QDialog(parent), numHists(num)
{
	label = new QLabel(tr("Set Histogram Range to Load (Max Number = " + QString::number(numHists) + "):"));
	
	labelLow = new QLabel(tr("From:"));
	lineLow = new QLineEdit;
	lineLow->setText("0");
	labelLow->setBuddy(lineLow);
	
	labelHigh = new QLabel(tr("To:"));
	lineHigh = new QLineEdit;
	lineHigh->setText(QString::number(numHists));
	labelHigh->setBuddy(lineHigh);

    checkFilter = new QCheckBox(tr("Replace large abs. values with a constant"));
	labelFilterMaximum = new QLabel(tr("Maximum value"));
	lineFilterMaximum = new QLineEdit;   
    lineFilterMaximum->setText("10000.");
	labelFilterMaximum->setBuddy(lineFilterMaximum);
    enableFilter(QCheckBox::Off);
	
	okButton = new QPushButton(tr("OK"));
	okButton->setDefault(true);
	cancelButton = new QPushButton(tr("Cancel"));

	connect(cancelButton, SIGNAL(clicked()), this, SLOT(reject()));
	connect(okButton, SIGNAL(clicked()), this, SLOT(okClicked()));
	connect(checkFilter, SIGNAL(stateChanged(int)), this, SLOT(enableFilter(int)));
	
	//Set the appearance
	QHBoxLayout *topRowLayout = new QHBoxLayout;
	topRowLayout->addWidget(label);
	
	QHBoxLayout *middleRowLayout = new QHBoxLayout;
	middleRowLayout->addWidget(labelLow);
	middleRowLayout->addWidget(lineLow);
	middleRowLayout->addWidget(labelHigh);
	middleRowLayout->addWidget(lineHigh);

    QVBoxLayout *filterLayout = new QVBoxLayout;
	filterLayout->addWidget(checkFilter);
	filterLayout->addWidget(labelFilterMaximum);
	filterLayout->addWidget(lineFilterMaximum);
	
	QHBoxLayout *bottomRowLayout = new QHBoxLayout;
	bottomRowLayout->addStretch();
	bottomRowLayout->addWidget(cancelButton);
	bottomRowLayout->addWidget(okButton);
	
	QVBoxLayout *mainLayout = new QVBoxLayout;
	mainLayout->addLayout(topRowLayout);
	mainLayout->addLayout(middleRowLayout);
	mainLayout->addLayout(filterLayout);
	mainLayout->addLayout(bottomRowLayout);
	
	setLayout(mainLayout);
	setWindowTitle(tr("Set Histogram Range"));
	setFixedHeight(sizeHint().height());
}

ImportWorkspaceDlg::~ImportWorkspaceDlg()
{
	
}

void ImportWorkspaceDlg::okClicked()
{
	if (!lineLow->text().isNull() && !lineLow->text().isEmpty() && !lineHigh->text().isNull() && !lineHigh->text().isEmpty())
	{
		//Check range is valid
		bool ok;
		int low = lineLow->text().toInt(&ok, 10); 
		
		if (!ok || low < 0 || low > numHists)
		{
			QMessageBox::warning(this, tr("Mantid"),
                   		tr("Lower limit is not valid - please change it.\n")
                    		, QMessageBox::Ok, QMessageBox::Ok);
			return;
		}
		
		int high = lineHigh->text().toInt(&ok, 10); 
		
		if (!ok || high < 0 || high > numHists)
		{
			QMessageBox::warning(this, tr("Mantid"),
                   		tr("Upper limit is not valid - please change it.\n")
                    		, QMessageBox::Ok, QMessageBox::Ok);
			return;
		}
		
		if (high < low)
		{
			lowerLimit = high;
			upperLimit = low;
		}
		else
		{
			lowerLimit = low;
			upperLimit = high;
		}

        if (checkFilter->checkState() == Qt::Checked)
        {
            filtered = true;
            maxValue = lineFilterMaximum->text().toDouble(&ok); 
		    if (!ok || maxValue < 0)
		    {
		    	QMessageBox::warning(this, tr("Mantid"),
                   		tr("Maximum value is not valid - please change it.\n")
                    		, QMessageBox::Ok, QMessageBox::Ok);
	    		return;
            }
        }
        else
        {
            filtered = false;
            maxValue = 0.; 
        }
		
		accept();
	}
}

void ImportWorkspaceDlg::enableFilter(int state)
{
    if (state == QCheckBox::Off) lineFilterMaximum->setReadOnly(true);
    if (state == QCheckBox::On ) lineFilterMaximum->setReadOnly(false);
}

