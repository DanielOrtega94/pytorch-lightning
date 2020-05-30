import torch
from pytorch_lightning.core.lightning import LightningModule
from pytorch_lightning.core.step_result import TrainResult, EvalResult
from torch.utils.data import Dataset, DataLoader
import numpy as np


class DeterministicModel(LightningModule):

    def __init__(self, weights=None):
        super().__init__()
        if weights is None:
            weights = torch.tensor([
                [4, 3, 5],
                [10, 11, 13]
            ])
        self.l1 = weights

    def forward(self, x):
        return self.l1.mm(x)

    def base_eval_result(self, acc):
        x = acc
        result = TrainResult(
            minimize=acc,
            early_stop_on=torch.tensor(1.4).type_as(x),
            checkpoint_on=torch.tensor(1.5).type_as(x)
        )

        result.log('log_acc1', torch.tensor(12).type_as(x))
        result.log('log_acc2', torch.tensor(7).type_as(x))
        result.to_pbar('pbar_acc1', torch.tensor(17).type_as(x))
        result.to_pbar('pbar_acc2', torch.tensor(19).type_as(x))
        return result

    def step(self, batch):
        x, y = batch
        y_hat = self(x)
        acc = torch.all(y_hat, y)
        return acc

    def training_step_only(self, batch, batch_idx):
        acc = self.step(batch)

        result = self.base_eval_result(acc)
        return result

    def training_step_with_batch_end(self, batch, batch_idx):
        acc = self.step(batch)

        result = self.base_eval_result(acc)
        result.pass_to_batch_end('to_batch_end_1', torch.tensor([-1, -2, -3]).type_as(x))

        return result

    def training_step_with_epoch_end(self, batch, batch_idx):
        acc = self.step(batch)

        result = self.base_eval_result(acc)
        result.pass_to_epoch_end('to_epoch_end_1', torch.tensor([-3, -2, -3]).type_as(x))

        return result

    def training_step_with_batch_and_epoch_end(self, batch, batch_idx):
        acc = self.step(batch)

        result = self.base_eval_result(acc)
        result.pass_to_batch_end('to_batch_end_1', torch.tensor([-1, -2, -3]).type_as(x))
        result.pass_to_epoch_end('to_epoch_end_1', torch.tensor([-3, -2, -3]).type_as(x))

        return result

    def training_step_dict_return(self, batch, batch_idx):
        acc = self.step(batch)

        logs = {'log_acc1': torch.tensor(12).type_as(x), 'log_acc2': torch.tensor(7).type_as(x)}
        pbar = {'pbar_acc1': torch.tensor(17).type_as(x), 'pbar_acc2': torch.tensor(19).type_as(x)}
        return {'loss': acc, 'log': logs, 'progress_bar': pbar}

    def training_step_end(self, outputs):
        if self.use_dp or self.use_ddp2:
            pass
        else:
            # only saw 3 batches
            assert len(outputs) == 3
            for batch_out in outputs:
                assert len(batch_out.keys()) == 2
                keys = ['to_batch_end_1', 'to_batch_end_2', 'minimize']
                for key in keys:
                    assert key in batch_out

        result = TrainResult()
        result.pass_to_epoch_end('from_train_step_end', torch.tensor(19))

    def training_epoch_end(self, outputs):
        if self.use_dp or self.use_ddp2:
            pass
        else:
            # only saw 3 batches
            assert len(outputs) == 3
            for batch_out in outputs:
                assert len(batch_out.keys()) == 2
                keys = ['to_batch_end_1', 'to_batch_end_2']
                for key in keys:
                    assert key in batch_out

    def train_dataloader(self):
        return DataLoader(DummyDataset(), batch_size=3, shuffle=False)

    def val_dataloader(self):
        return DataLoader(DummyDataset(), batch_size=3, shuffle=False)

    def test_dataloader(self):
        return DataLoader(DummyDataset(), batch_size=3, shuffle=False)


class DummyDataset(Dataset):

    def __len__(self):
        return 12

    def __getitem__(self, idx):
        return np.array([0.5, 1.0, 2.0])